import numpy as np
import matplotlib.pyplot as plt
import sys
from .model import *
from .utils import *

# note: start time should be zero do not change it!
START_TIME = 0 
END_TIME = 5

class Simulator():
    def __init__(self, start_time, end_time, packet_list, BW, cc, threshold):
        self.global_time = start_time
        self.global_end = end_time * 1000 # ms
        self.cc = cc
        self.threshold = threshold
        _duration = end_time - start_time
        
        # time slice for x
        _time_slice = np.linspace(start_time, end_time, int(_duration/mSecond(1)))
        
        ###################### IMPLEMENT #############################
        # implement bandwidth with gamma distribution
        # hint 1: use gamma distribution method in problem 1
        # hint 2: using _time_slice, alpha, beta and also argument BW
        ##############################################################
        uplink_alpha = 3; uplink_beta =1
        downlink_alpha = 3.5; downlink_beta = 2
        uplink = stats.gamma.pdf(x=_time_slice, a = uplink_alpha, scale = uplink_beta)
        downlink = stats.gamma.pdf(x=_time_slice, a = downlink_alpha, scale = downlink_beta)
        self.uplink_bw = [x * BW for x in uplink]
        self.downlink_bw = [x * BW for x in downlink]
        
        
        # define sender, receiver, and base station for simulation
        self.bs = BaseStation("bs", self.threshold)
        self.senders = Client(src = "send", dst="recv", bandwidth = self.uplink_bw, pkt_list = packet_list, cc=cc)
        self.receivers = Client(src = "recv", dst="send", bandwidth = self.downlink_bw, cc=cc)
        
        # member variables for logging
        self.queue_length = []
        self.avgRTT = []
        self.cwnd = []
        self.loss = []
        self.retx = []
        self.recv = []
        self.sender_retx =  []
        # member variable for uplink & downlink simulation
        self.up_ongoing = []
        self.down_ongoing = [] 
        self.ack_ongoing = []

    def timer(self):
        self.global_time += int(1) # ms
    
    def execute(self):
        while (self.global_time < self.global_end):
            # 1. sender send pkts to bs at time t
            pkts = self.senders.send(self.global_time)

            # 2. return the pkts to bs when bs_arrival time == t
            uplink_arrivals = self.uplink_ongoing(self.global_time, pkts)
            
            # 3. bs admit packets from sender and send pkts to receiver  
            admit, loss = self.bs.admit(self.global_time, uplink_arrivals, self.receivers.channel)
            
            # 4. return the admitted pkts to receiver when recv_arrival == t
            downlink_arrivals = self.downlink_ongoing(self.global_time, admit)
            
            # 3. receiver receives pkts from bs and send acks to sender
            acks = self.receivers.recv(self.global_time, downlink_arrivals)

            # 4. sender get acks from receiver 
            ack_arrivals = self.acknowledge_ongoing(self.global_time, acks)

            # 5. sender process's congestion control
            done = self.senders.congestion_control(self.global_time, ack_arrivals)
            
            if done == True:
                print("simulation done at time: ", mSecond(self.global_time))
            
            # logging
            self.logging("Loss", len(loss))
            self.logging("RTT", self.senders.avgRTT)
            self.logging("CWND", self.senders.cwnd)
            self.logging("Queue Length", len(self.bs.queued))
            self.logging("retx", self.receivers.retx)
            self.logging("recv", self.receivers.ack_sequence)
            self.logging("sender_retx", self.senders.retx)
            # global timer
            self.timer()
        
        # ack_sequence modifyed
        print("# of transmitted packets: ", self.receivers.ack_sequence)

        
        _duration = END_TIME - START_TIME
        _time_slice = np.linspace(START_TIME, END_TIME, int(_duration/mSecond(1)))
        
        plot_list= []
        plot_list.append(Plotter(0, 0, "Loss", _time_slice, self.loss))
        plot_list.append(Plotter(0, 1, "Queue Length", _time_slice, self.queue_length))
        plot_list.append(Plotter(0, 2, "avgRTT", _time_slice, self.avgRTT))
        plot_list.append(Plotter(1, 0, "retx_cdf", _time_slice, self.retx))
        #plot_list.append(Plotter(1, 0, "retx_mine", _time_slice, self.sender_retx))
        
        plot_list.append(Plotter(1, 1, "recv packet", _time_slice, self.recv))
        #plot_list.append(Plotter(1, 1, "network", _time_slice, self.uplink_bw, self.downlink_bw))
        plot_list.append(Plotter(1, 2, "CWND", _time_slice, self.cwnd))
        
        graphPlot(self.cc, self.threshold, plot_list)
        
        # data saving
        if 0:
            f1 = open("./LOG/LOSS_LOG.txt", 'w')
            f2 = open("./LOG/Queue_length_LOG.txt", 'w')
            f3 = open("./LOG/avgrtt_LOG.txt.txt", 'w')
            f4 = open("./LOG/RETX_LOG.txt", 'w')
            f5 = open("./LOG/SENDER_RETX_LOG.txt", 'w')
            f6 = open("./LOG/RECV_LOG.txt", 'w')
            f7 = open("./LOG/UPLINK_BW_LOG.txt", 'w')
            f8 = open("./LOG/DOWNLINK_BW_LOG.txt", 'w')
            f9 = open("./LOG/CWND_LOG.txt", 'w')
            original_stdout = sys.stdout
            sys.stdout = f1
            print("[LOSS LOG]")
            print(self.loss)
            sys.stdout = f2
            print("[QUEUE LENGTH LOG]")
            print(self.queue_length)
            sys.stdout = f3
            print("[AVGRTT LOG]")
            print(self.avgRTT)
            sys.stdout = f4
            print("[RETX LOG]")
            print(self.retx)
            sys.stdout = f5
            print("[SENDER RETX LOG]")
            print(self.sender_retx)
            sys.stdout = f6
            print("[RECV LOG]")
            print(self.recv)
            sys.stdout = f7
            print("[UPLINK BW LOG]")
            print(self.uplink_bw)
            sys.stdout = f8
            print("DONWLINK BW LOG]")
            print(self.downlink_bw)
            sys.stdout = f9
            print("[CWND LOG]")
            print(self.cwnd)
            sys.stdout =original_stdout
            f1.close()
            f2.close()
            f3.close()
            f4.close()
            f5.close()
            f6.close()
            f7.close()
            f8.close()
            f9.close()
        
        
        return
    
    def uplink_ongoing(self, t, pkts):
        arrival_list = []
        
        for u in pkts:
            self.up_ongoing.append(u)
        
        tmp = self.up_ongoing.copy()

        for p in self.up_ongoing:
            if p.bs_arrival == t:
                arrival_list.append(p)
                tmp.remove(p)
            else:
                continue
        
        self.up_ongoing = tmp

        return arrival_list
    
    def downlink_ongoing(self, t, pkts):
        arrival_list = []

        for d in pkts:
            self.down_ongoing.append(d)
        
        tmp = self.down_ongoing.copy()

        for p in self.down_ongoing:
            if p.recv_arrival == t:
                arrival_list.append(p)
                tmp.remove(p)
            else:
                continue
        self.down_ongoing = tmp

        return arrival_list
    
    def acknowledge_ongoing(self, t, ack):
        if ack == False and len(self.ack_ongoing) == 0:
            return False

        if ack != False:
            self.ack_ongoing.append(ack)
        
        ack = False
        
        for p in self.ack_ongoing:
            if p.ack_arrival == t:
                ack = p
            else:
                continue
        
        return ack

    def logging(self, x, data):
        if x == "Loss":
            self.loss.append(data)
        if x == "Queue Length":
            self.queue_length.append(data)
        if x == "RTT":
            self.avgRTT.append(data)
        if x == "CWND":
            self.cwnd.append(data)
        if x == "retx":
            self.retx.append(data)
        if x == "recv":
            self.recv.append(data)
        if x == "sender_retx":
            self.sender_retx.append(data)