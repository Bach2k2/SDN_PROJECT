from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

# Import the mitigation module or no mitigation from the controller folder
import mitigation_module
from datetime import datetime
import pandas as pd
import numpy as np
import socket
import struct
import joblib
from tensorflow.keras.models import load_model
from sklearn.metrics import confusion_matrix, classification_report


class DDosMonitor01(mitigation_module.SimpleSwitch13):

    def __init__(self, *args, **kwargs):

        super(DDosMonitor01, self).__init__(*args, **kwargs)
        self.datapaths = {}

        self.monitor_thread = hub.spawn(self._monitor)

        file0 = open("PredictFlowStatsfile.csv", "w")
        file0.write('timestamp,datapath_id,flow_id,ip_src,tp_src,ip_dst,tp_dst,ip_proto,icmp_code,icmp_type,flow_duration_sec,flow_duration_nsec,idle_timeout,hard_timeout,flags,packet_count,byte_count,packet_count_per_second,packet_count_per_nsecond,byte_count_per_second,byte_count_per_nsecond\n')
        file0.close()

        self.scalar = None
        self.model_lstm = None
        start = datetime.now()

        self.load_model()

        end = datetime.now()
        print("Loading time: ", (end-start))

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

            print("Predicting model...")
            self.flow_predict()

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):

        timestamp = datetime.now()
        timestamp = timestamp.timestamp()

        file0 = open("PredictFlowStatsfile.csv", "a+")

        body = ev.msg.body
        icmp_code = -1
        icmp_type = -1
        tp_src = 0
        tp_dst = 0

        for stat in sorted([flow for flow in body if (flow.priority == 1)], key=lambda flow:
                           (flow.match['eth_type'], flow.match['ipv4_src'], flow.match['ipv4_dst'], flow.match['ip_proto'])):

            ip_src = stat.match['ipv4_src']
            ip_dst = stat.match['ipv4_dst']
            ip_proto = stat.match['ip_proto']

            if stat.match['ip_proto'] == 1:
                icmp_code = stat.match['icmpv4_code']
                icmp_type = stat.match['icmpv4_type']

            elif stat.match['ip_proto'] == 6:
                tp_src = stat.match['tcp_src']
                tp_dst = stat.match['tcp_dst']

            elif stat.match['ip_proto'] == 17:
                tp_src = stat.match['udp_src']
                tp_dst = stat.match['udp_dst']

            flow_id = str(ip_src) + str(tp_src) + str(ip_dst) + \
                str(tp_dst) + str(ip_proto)

            try:
                packet_count_per_second = stat.packet_count/stat.duration_sec
                packet_count_per_nsecond = stat.packet_count/stat.duration_nsec
            except:
                packet_count_per_second = 0
                packet_count_per_nsecond = 0

            try:
                byte_count_per_second = stat.byte_count/stat.duration_sec
                byte_count_per_nsecond = stat.byte_count/stat.duration_nsec
            except:
                byte_count_per_second = 0
                byte_count_per_nsecond = 0

            file0.write("{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n"
                        .format(timestamp, ev.msg.datapath.id, flow_id, ip_src, tp_src, ip_dst, tp_dst,
                                stat.match['ip_proto'], icmp_code, icmp_type,
                                stat.duration_sec, stat.duration_nsec,
                                stat.idle_timeout, stat.hard_timeout,
                                stat.flags, stat.packet_count, stat.byte_count,
                                packet_count_per_second, packet_count_per_nsecond,
                                byte_count_per_second, byte_count_per_nsecond))

        file0.close()

    def load_model(self):
        self.logger.info("Loading model...")
        _lstm_model = load_model('best_lstm_model.h5')
        self.model_lstm = _lstm_model

        # Usage
        new_df = self.process_traffic_data(
            'Traffic_sample.csv', ['flow_id'], 'ip_src', 'ip_dst')

        x = new_df.iloc[:, :-1].values
        x = x.astype('float64')
        y = new_df.label

        predict = self.model_lstm.predict(x)
        predict = np.round(predict)
        print(confusion_matrix(y, predict), classification_report(y, predict))

        self.logger.info(
            "------------------------------------------------------------------------------")

    def process_traffic_data(self, file_path, columns_to_drop, src_col, dst_col):
        # Read the data from the CSV file
        df = pd.read_csv(file_path)

        # Drop specified columns
        df = df.drop(columns_to_drop, axis='columns')

        # Function to convert IP to integer
        def ip_to_int(ip):
            return struct.unpack("!I", socket.inet_aton(ip))[0]

        # Apply ip_to_int to specified columns
        df[src_col] = df[src_col].apply(ip_to_int).astype(str)
        df[dst_col] = df[dst_col].apply(ip_to_int).astype(str)

        return df

    def flow_predict(self):
        try:
            def int_to_ip(ip_int):
                return socket.inet_ntoa(struct.pack("!I", ip_int))

            predict_flow_dataset = self.process_traffic_data(
                'PredictFlowStatsfile.csv', ['flow_id'], 'ip_src', 'ip_dst')

            # X_predict_flow = self.scalar.transform(predict_flow_dataset)
            X_predict_flow = predict_flow_dataset.iloc[:, :].values
            X_predict_flow = X_predict_flow.astype('float64')
            if (len(X_predict_flow) <= 0):
                raise ValueError("No packets available for processing.")
            y_flow_pred = self.model_lstm.predict(X_predict_flow)
            y_flow_pred = np.round(y_flow_pred).astype(int)
            y_flow_pred = y_flow_pred.flatten()
            y_flow_pred = y_flow_pred.tolist()
            legitimate_trafic = 0
            ddos_trafic = 0
            n = 0

            for i in y_flow_pred:
                if i == 0:
                    legitimate_trafic = legitimate_trafic + 1
                else:
                    ddos_trafic = ddos_trafic + 1
                    victim = int_to_ip(int(predict_flow_dataset.ip_dst[n]))
                n += 1

            self.logger.info("legitimate_trafic: {}, ddos_trafic: {}".format(legitimate_trafic, ddos_trafic))
            self.logger.info(
                "------------------------------------------------------------------------------")
            if (legitimate_trafic/len(y_flow_pred)*100) > 80:
                self.logger.info("Normal Traffic")
            else:
                self.logger.info(
                    "Attack DDOS at host {} have ip address {}".format(victim, victim))
                self.mitigation = 1
            self.logger.info(
                "------------------------------------------------------------------------------")

            file0 = open("PredictFlowStatsfile.csv", "w")

            file0.write('timestamp,datapath_id,flow_id,ip_src,tp_src,ip_dst,tp_dst,ip_proto,icmp_code,icmp_type,flow_duration_sec,flow_duration_nsec,idle_timeout,hard_timeout,flags,packet_count,byte_count,packet_count_per_second,packet_count_per_nsecond,byte_count_per_second,byte_count_per_nsecond\n')
            file0.close()

        except Exception as e:
            self.logger.info(f"An error occurred: {e}")
            pass

