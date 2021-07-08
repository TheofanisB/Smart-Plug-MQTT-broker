import paho.mqtt.client as mqtt
import ssl
import sys
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from threading import Timer
from datetime import datetime


class IoTExample:
    def __init__(self):
        self.ax = None
        self._establish_mqtt_connection()
        self._prepare_graph_window()

    def start(self): #Starting the loop
        if self.ax:
            self.client.loop_start()
            plt.show()
        else:
            self.client.loop_forever()

    def disconnect(self, args=None):
        self.client.disconnect()  # disconnect

    def _establish_mqtt_connection(self): #Connecting client to the Smart Plug by using the MQTT Broker
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_log = self._on_log
        self.client.on_message = self._on_message

        print('Trying to connect to MQTT server...')
        self.client.tls_set_context(ssl.SSLContext(ssl.PROTOCOL_TLSv1_2))
        self.client.username_pw_set('username', 'password')
        self.client.connect('server_ip', 8883)

    def _on_connect(self, client, userdata, flags, rc):
        print('Connected with result code '+str(rc))

        # Subscribing in _on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(
            'hscnl/hscnl02/state/ZWaveNode005_ElectricMeterWatts/state')
        client.subscribe('hscnl/hscnl02/command/ZWaveNode005_Switch/command')
        client.subscribe('hscnl/hscnl02/state/ZWaveNode005_Switch/state')
        # client.subscribe('hscnl/hscnl02/#/#/#')

    # The callback for when a PUBLISH message is received from the server.
    def _on_message(self, client, userdata, msg):
        if msg.topic == 'hscnl/hscnl02/state/ZWaveNode005_ElectricMeterWatts/state':
            self._add_value_to_plot(float(msg.payload))
        print(msg.topic+' '+str(msg.payload))

    def _on_log(self, client, userdata, level, buf):
        print('log: ', buf)

    def _prepare_graph_window(self):
        # Plot variables
        plt.rcParams['toolbar'] = 'None'
        plt.title('Node 005 Power Consumption Chart  by TheoB')  # Title
        plt.ylabel('Watts')  # Wattage label for the Y Axis
        plt.xlabel('Timestamp')  # Time Label for the X Axis
        plt.tight_layout  # Adding Support for smaller screen devices
        plt.grid(True)  # Adding a grid to the plot
        self.ax = plt.subplot(111)
        self.dataX = []
        self.dataY = []
        self.first_ts = datetime.now()
        self.lineplot, = self.ax.plot(
            self.dataX, self.dataY, linestyle='--', marker='o', color='c')  # double  dash line , o Marker and Cyan colored lines
        self.ax.figure.canvas.mpl_connect('close_event', self.disconnect)
        self.ax.set_facecolor('#d3d3d3')  # background color of the chart
        self.finishing = False
        self._my_timer()

    def _refresh_plot(self): # function that refreshes the displayed plot
        if len(self.dataX) > 0:
            self.ax.set_xlim(min(self.first_ts, min(self.dataX)),
                             max(max(self.dataX), datetime.now()))
            self.ax.set_ylim(min(self.dataY) * 0.8, max(self.dataY) * 1.2)
            self.ax.relim()
        else:
            self.ax.set_xlim(self.first_ts, datetime.now())
            self.ax.relim()
        plt.draw()

    def _add_value_to_plot(self, value): 
        self.dataX.append(datetime.now())
        self.dataY.append(value)
        self.lineplot.set_data(self.dataX, self.dataY)
        self._refresh_plot()

    def _my_timer(self):
        self._refresh_plot()
        if not self.finishing:
            # Adding another timestamp every 0.5 secs
            Timer(0.5, self._my_timer).start()


try:
    iot_example = IoTExample()
    iot_example.start()
except KeyboardInterrupt:
    print('Interrupted')
    try:
        iot_example.disconnect()
        sys.exit(0)
    except SystemExit:
        os._exit(0)
