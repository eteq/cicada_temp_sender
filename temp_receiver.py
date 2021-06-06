
# Copyright 2021 Erik Tollerud and Marie van Staveren

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import board
import busio
import digitalio
import adafruit_rfm69
import datetime

DEFAULT_ENCRYPTION = b'radioplusTCiscoo'


class TempReceiver:
    """
    Receives messages of the form "TempU:##.##,Vbat:###.##"
    and logs them
    """
    def __init__(self, cspin=board.D16, resetpin=board.D13, spinum=1, freq=433.0, verbose=False):
        self.verbose = verbose

        cs = digitalio.DigitalInOut(cspin)
        reset = digitalio.DigitalInOut(resetpin)
        if spinum==0:
            suffix = ''
        else:
            suffix = '_' + str(spinum)
        sck = getattr(board, 'SCK' + suffix)
        mosi = getattr(board, 'MOSI' + suffix)
        miso = getattr(board, 'MISO' + suffix)
        spi = busio.SPI(sck, MOSI=mosi, MISO=miso)

        rfm69 = adafruit_rfm69.RFM69(spi, cs, reset, freq,
                                     encryption_key=DEFAULT_ENCRYPTION)
        print('rfm69 started')
        self.rfm69 = rfm69

    def get_data(self, **recv_kwargs):
        msg = self.rfm69.receive(**recv_kwargs)
        if self.verbose:
            print('Message: "{}"'.format(msg))
        if msg.startswith(b'TempC:'):
            # valid
            floats = [float(c.split(b':')[1]) for c in msg.split(b',')]
            return tuple(floats)
        else:
            raise ValueError('Did not get a valid message')

    def temp_log(self, timeout=61, fnout=None, n=None):
        headerline = 'timestamp temp_c vbat nmsg rssi'
        if fnout is None:
            f = None
        else:
            if not os.path.exists(fnout):
                with open(fnout, 'w') as f:
                    f.write(headerline + '\n')
            print(headerline)

            f = open(fnout, 'a')
        try:
            i = 0
            while n is None or i < n:
                try:
                    temp_c, v_bat, nmsg = self.get_data(timeout=timeout)
                    dt = datetime.datetime.now()

                    line = str(dt).replace(' ', 'T')
                    line += ' ' + str(temp_c)
                    line += ' ' + str(v_bat)
                    line += ' ' + str(int(nmsg))
                    line += ' ' + str(self.rfm69.last_rssi)
                    print(line)
                    if f is not None:
                        f.write(line)
                        f.write('\n')
                        f.flush()
                except Exception as e:
                    print('Msg receipt failed due to', e)
                i += 1
        finally:
            if f is not None:
                f.close()


    @staticmethod
    def deg_c_to_f(degc):
        return degc*1.8 + 32

if __name__ == '__main__':
    r = TempReceiver(verbose=False)

    if len(sys.argv) == 1:
        r.temp_log(n=5)
    elif len(sys.argv) == 2:
        r.temp_log(fnout=sys.argv[1])
    else:
        print('invalid argvs')
        sys.exit(1)
