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
    def __init__(self, cspin=board.D16, resetpin=board.D13, spinum=1, freq=433.0):
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
        if msg.startswith(b'TempC:'):
            # valid
            floats = [float(c.split(b':')[1]) for c in msg.split(b',')]
            return tuple(floats)
        else:
            raise ValueError('Did not get a valid message')

    def temp_log(self, timeout=61, fnout=None, n=None):

        if fnout is None:
            f = None
        else:
            if not os.path.exists(fnout):
                with open(fnout, 'w') as f:
                    f.write('timestamp temp_c vbat nmsg rssi\n')

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
                    line += ' ' + str(nmsg)
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
    r = TempReceiver()

    if len(sys.argv) == 1:
        r.temp_log(n=5)
    elif len(sys.argv) == 2:
        r.temp_log(fnout=sys.argv[1])
    else:
        print('invalid argvs')
        sys.exit(1)