#
# Copyright (C) 2013 Stefan Taferner <stefan.taferner@gmx.at>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#

# KNX/EIB protocol decoder

import sigrokdecode as srd

# Used for differentiating between the two data directions.
KNX_RX = 0
KNX_TX = 1


class Decoder(srd.Decoder):
    api_version = 3
    id = 'knx'
    name = 'KNX'
    longname = 'KNX/EIB bus protocol'
    desc = 'KNX/EIB home automation bus.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['knx']
    tags = ['Automation']
    # channels = (
    #    {'id': 'bus', 'name': 'KNX', 'desc': 'KNX bus line'},
    # )
    optional_channels = (
        # Allow specifying only one of the signals, e.g. if only one data
        # direction exists (or is relevant).
        {'id': 'rx', 'name': 'Rx', 'desc': 'KNX receive line'},
        {'id': 'tx', 'name': 'Tx', 'desc': 'KNX transmit line'},
    )
    options = (
        {'id': 'timings', 'desc': 'Bit timings',
                          'default': 'default', 'values': ('strict', 'default', 'relaxed')},
        {'id': 'inverted_signal', 'desc': 'Inverted signal', 'default': 'no', 'values': ('yes', 'no')},
    )

    annotations = (
        ('telegram-error', 'Telegram byte with parity error'),  # 0
        ('telegram', 'Telegram'),                               # 1
        ('telegram-checksum', 'Telegram checksum byte'),        # 2
        ('telegram-checksum-error', 'Telegram checksum byte with wrong checksum'),  # 3
        ('acknowledge-ack', 'Acknowledged'),                    # 4
        ('acknowledge-nak', 'Not acknowledged'),                # 5
        ('acknowledge-busy', 'Receiver busy'),                  # 6
        ('random-byte', 'Random byte'),                         # 7
        ('err-timing', 'Time between transmissions violated'),  # 8
        ('warnings', 'Human-readable warnings'),                # 9
        ('bytes', 'Bytes on the KNX bus'),                      # 10
        ('acknowledge-frame', 'Short acknowledge frame'),       # 11
        ('acknowledge-busy-nack', 'BUSY-NAK collision'),        # 12
    )

    # these must match order of above annotations
    rowid_byte_parity_error = 0
    rowid_databyte = 1
    rowid_checksum = 2
    rowid_checksum_error = 3
    rowid_ack = 4
    rowid_nack = 5
    rowid_busy = 6
    rowid_random_byte = 7
    rowid_error_timing = 8
    rowid_error = 9
    rowid_label = 10
    rowid_label_ack = 11
    rowid_busy_nack = 12

    annotation_rows = (
         ('id-telegram', 'Telegram', (rowid_label, rowid_label_ack)),
         ('id-bytes', 'Bytes', (rowid_databyte, rowid_checksum, rowid_ack, rowid_nack, rowid_busy, rowid_busy_nack)),
         ('id-warnings', 'Warnings', (rowid_error, rowid_byte_parity_error, rowid_checksum_error,
                                      rowid_random_byte, rowid_error_timing)),
    )

    def __init__(self, **kwargs):
        # Constructor
        self.data = 0
        self.ss = 0
        self.samplerate = None
        self.bitrate = 9600
        self.state = 'IDLE'    # The state of the decoder
        self.start_sample = 0  # The samplenum of the start sample
        self.end_sample = 0
        self.next_min = 0
        self.next_max = 0
        self.last_bus = 1
        self.samples_per_usec = -1
        self.inverted_signal = False
        self.bit_samples = -1
        self.stop_samples = -1
        self.byte_samples = -1
        self.bit_samples_min = -1
        self.bit_samples_max = -1
        self.byte_samples_min = -1
        self.byte_samples_max = -1
        self.bit_offs_min = -1
        self.bit_offs_max = -1
        self.ack_wait_samples_min = -1
        self.ack_wait_samples_max = -1
        self.tel_wait_samples_min = -1
        self.byte_end_sample = -1
        self.checksum = 0xff
        self.telegram = []
        self.telegram_bytes = -1
        self.telegram_valid = False
        self.byte0_start_sample = -1
        self.byte = 0
        self.mask = 0
        self.parity = False
        self.reset()

    def metadata(self, key, value):
        # Set a metadata value
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
            self.samples_per_usec = float(self.samplerate / 1000000.0)
            # print("{0} samples per usec".format(self.samples_per_usec))

    def reset(self):
        # Reset internal decoder values
        print('reset')
        self.data = 0
        self.ss = 0
        self.samplerate = None
        self.bitrate = 9600
        self.state = 'IDLE'    # The state of the decoder
        self.start_sample = 0  # The samplenum of the start sample
        self.end_sample = 0
        self.next_min = 0
        self.next_max = 0
        self.last_bus = 1

    def start(self):
        # Start decoding
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)

        self.inverted_signal = (self.options['inverted_signal'] == 'yes')
        self.bit_samples = int(self.samplerate / self.bitrate)  # 104 usec (for standard 9600 baud)
        self.stop_samples = int(self.bit_samples * 3)
        self.byte_samples = self.bit_samples * 13

        if self.options['timings'] == 'strict':
            self.bit_samples_min = self.bit_samples - 2 * self.samples_per_usec - 1
            self.bit_samples_max = self.bit_samples + 2 * self.samples_per_usec + 1
            self.byte_samples_min = self.byte_samples - 30 * self.samples_per_usec - 1
            self.byte_samples_max = self.byte_samples + 30 * self.samples_per_usec + 1
            self.bit_offs_min = int(-7 * self.samples_per_usec) - 1
            self.bit_offs_max = int(33 * self.samples_per_usec) + 1
        elif self.options['timings'] == 'relaxed':
            self.bit_samples_min = self.bit_samples - 20 * self.samples_per_usec
            self.bit_samples_max = self.bit_samples + 20 * self.samples_per_usec
            self.byte_samples_min = self.byte_samples - 40 * self.samples_per_usec
            self.byte_samples_max = self.byte_samples + 60 * self.samples_per_usec
            self.bit_offs_min = int(-9 * self.samples_per_usec)
            self.bit_offs_max = int(40 * self.samples_per_usec)
        else:  # 'default' timings
            self.bit_samples_min = self.bit_samples - 2 * self.samples_per_usec - 1
            self.bit_samples_max = self.bit_samples + 2 * self.samples_per_usec + 1
            self.byte_samples_min = self.byte_samples - 30 * self.samples_per_usec - 3
            self.byte_samples_max = self.byte_samples + 30 * self.samples_per_usec + 5
            self.bit_offs_min = int(-9 * self.samples_per_usec) - 1
            self.bit_offs_max = int(40 * self.samples_per_usec) + 2

        # See KNX docu 3/2/2 p. 32+ for timings
        # The end of byte is 2 bit-times too late in the algorythm. Therefore the lower values below.
        self.ack_wait_samples_min = self.bit_samples * 13 - 50 * self.samples_per_usec
        self.ack_wait_samples_max = self.bit_samples * 13 + 50 * self.samples_per_usec
        self.tel_wait_samples_min = self.bit_samples * 38

        if self.inverted_signal:
            self.last_bus = 0
        else:
            self.last_bus = 1

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')

        has_pin = [self.has_channel(ch) for ch in (KNX_RX, KNX_TX)]
        if not True in has_pin:
            raise ChannelError('Need at least one of KNX TX or RX pins.')

        while True:
            # wait_conditions = []
            # if has_pin[KNX_RX]:
            #    pass

            # if has_pin[KNX_TX]:
            #    pass

            # (rx, tx) = self.wait(wait_conditions)
            (bus, tx) = self.wait()

            if self.inverted_signal:
                bus = 1 - bus

            # Ignore spikes between expected signal parts
            if self.samplenum < self.next_min:
                continue

            falling_edge = (self.last_bus == 1 and bus == 0)
            self.last_bus = bus

            # Wait until the next falling edge occurs
            if not falling_edge and (self.next_max == 0 or self.samplenum < self.next_max):
                continue

            if self.state == 'BYTE_END':
                # print("  samplenum={0}, falling_edge={1:1}, parity={2:1}".format(self.samplenum,
                #                                                                  falling_edge, self.parity))
                self.byte &= 0xff
                self.checksum ^= self.byte
                self.telegram.append(self.byte)
                self.telegram_bytes += 1
                out = None

                if falling_edge:
                    self.byte_end_sample = self.samplenum
                else:
                    self.byte_end_sample = self.start_sample + self.byte_samples

                if not falling_edge:  # Timeout => end of transmission
                    if self.telegram_bytes <= 1:
                        if self.byte == 0xcc:
                            self.putx(self.start_sample, self.byte_end_sample, self.rowid_label_ack, 'ACK')
                            out = self.rowid_ack
                        elif self.byte == 0x0c:
                            self.putx(self.start_sample, self.byte_end_sample, self.rowid_label_ack, 'NAK')
                            out = self.rowid_nack
                        elif self.byte == 0xc0:
                            self.putx(self.start_sample, self.byte_end_sample, self.rowid_label_ack, 'BUSY')
                            out = self.rowid_busy
                        elif self.byte == 0x00:
                            self.putx(self.start_sample, self.byte_end_sample, self.rowid_label_ack, 'BUSY_NAK')
                            out = self.rowid_busy_nack
                        else:
                            self.putx(self.start_sample, self.byte_end_sample, self.rowid_random_byte, 'Ignored')
                            out = self.rowid_databyte
                    else:
                        if self.checksum != 0:
                            self.putx(self.start_sample, self.byte_end_sample, self.rowid_checksum_error,
                                      'Checksum Err')
                        out = self.rowid_checksum

                else:  # Not a timeout => another bit arrived
                    out = self.rowid_databyte

                if not self.parity:
                    self.putx(self.start_sample, self.byte_end_sample, self.rowid_error, 'Parity Err')
                    self.telegram_valid = False
                    out = self.rowid_databyte

                if out is not None:
                    self.putx(self.start_sample, self.byte_end_sample, out, '{0:02x}'.format(self.byte))

                if not falling_edge:  # Timeout => end of transmission
                    # if self.end_sample > 0:
                    #     wait = self.byte0_start_sample - self.end_sample
                    #     if self.telegram_bytes == 1:
                    #         if wait < self.ack_wait_samples_min:
                    #             self.put_err_timing(wait - self.ack_wait_samples_min)
                    #         elif wait > self.ack_wait_samples_max:
                    #             self.put_err_timing(wait - self.ack_wait_samples_max)
                    #     elif wait < self.tel_wait_samples_min:
                    #         self.put_err_timing(wait - self.tel_wait_samples_min)

                    if self.telegram_bytes >= 8:
                        self.put_telegram(self.byte0_start_sample, self.byte_end_sample, self.telegram)

                    self.next_min = 0
                    self.next_max = 0
                    self.state = 'IDLE'
                    self.end_sample = self.byte_end_sample
                    # print("  ** end of transmission")
                    continue

                self.state = 'START_BIT'

            if self.state == 'IDLE':
                self.state = 'START_BIT'
                self.checksum = 0xff
                self.telegram = []
                self.telegram_bytes = 0
                self.telegram_valid = True
                self.byte0_start_sample = self.samplenum

            if self.state == 'START_BIT' and falling_edge:
                self.byte = 0
                self.mask = 1
                self.parity = True
                self.state = 'BYTE'
                self.start_sample = self.samplenum
                self.next_min = self.start_sample + self.bit_samples + self.bit_offs_min
                self.next_max = self.start_sample + self.bit_samples + self.bit_offs_max
                # print("Start bit at {0}us".format(int(self.start_sample / self.samples_per_usec)))
                continue

            if self.state == 'BYTE':
                if not falling_edge:
                    self.byte |= self.mask
                    self.parity = not self.parity

                # print("  at +{0}us, falling_edge={1:1}, parity={2:1}, mask=0x{3:x},"
                #    .format(int((self.samplenum - self.start_sample) / self.samples_per_usec),
                #     falling_edge, self.parity, self.mask))

                if self.mask < 0x100:
                    self.mask <<= 1
                    self.next_min += self.bit_samples
                    self.next_max += self.bit_samples
                else:
                    self.state = 'BYTE_END'
                    self.next_min = self.start_sample + self.byte_samples_min
                    self.next_max = self.start_sample + self.byte_samples_max
                continue

    #
    # Output an annotation
    #
    def putx(self, ss, es, rowid, msg):
        self.put(ss, es, self.out_ann, [rowid, [msg]])

    #
    # Output the telegram
    #
    def put_telegram(self, ss, es, telegram):

        from_addr = str(telegram[1] >> 4) + "." + str(telegram[1] & 15) + "." + str(telegram[2])
        details = ''

        if telegram[5] & 128 == 0:
            dest_addr = str(telegram[3] >> 4) + "." + str(telegram[3] & 15) + "." + str(telegram[4])
            dest_is_group_addr = False
        else:
            dest_addr = str(telegram[3] >> 4) + "/" + str(telegram[3] & 15) + "/" + str(telegram[4])
            dest_is_group_addr = True

        use_apcf = False
        use_seq = False
        use_6bit_data = False

        if dest_is_group_addr:
            details = 'Group'
            use_apcf = True
        else:
            tpcf = telegram[6] & 0xc3   # The transport control field

            if tpcf == 0x80:            # T_Connect
                details = 'T_Connect'
            elif tpcf == 0x81:          # T_Disconnect
                details = 'T_Disconnect'
            elif tpcf == 0xc2:          # T_ACK
                details = 'T_ACK'
                use_seq = True
            elif tpcf == 0xc3:          # T_NAK
                details = 'T_NAK'
                use_seq = True
            elif tpcf & 0xc0 == 0x40:   # A connected data transfer
                details = ''
                use_seq = True
                use_apcf = True
            elif tpcf & 0xc0 == 0:      # An individual data transfer
                details = 'Individual'
                use_apcf = True

        details += ' '
        data = ''

        if use_apcf:
            apcf = ((telegram[6] & 3) << 8) | telegram[7]  # The application control field (10 bits)
            apcf_group = apcf >> 6
            apcf_type = apcf & 0x3f

            if apcf == 0:
                details += 'Value_Read'
            elif apcf_group == 0x1:
                details += 'Value_Response'
                data = self.telegram_group_value_data(telegram)
            elif apcf_group == 0x2:
                details += 'Value_Write'
                data = self.telegram_group_value_data(telegram)

            elif apcf_group == 0x3:
                details += 'Individual_Addr_Write'
            elif apcf_group == 0x4:
                details += 'Individual_Addr_Read'
            elif apcf_group == 0x5:
                details += 'Individual_Addr_Response'

            elif apcf_group == 0x6:
                details += 'ADC_Read'
                use_6bit_data = True
            elif apcf_group == 0x7:
                details += 'ADC_Response'
                use_6bit_data = True

            elif apcf_group == 0x8:
                details += 'Mem_Read'
            elif apcf_group == 0x9:
                details += 'Mem_Response'
            elif apcf_group == 0xa:
                details += 'Mem_Write'

            elif apcf_group == 0xb:
                if apcf_type == 0:
                    details += 'UserMem_Read'
                elif apcf_type == 1:
                    details += 'UserMem_Response'
                elif apcf_type == 2:
                    details += 'UserMem_Write'
                elif apcf_type == 4:
                    details += 'UserMemBit_Write'
                elif apcf_type == 5:
                    details += 'UserManufacturerInfo_Read'
                elif apcf_type == 6:
                    details += 'UserManufacturerInfo_Response'
                elif apcf_type == 7:
                    details += 'FunctionProperty_Command'
                elif apcf_type == 8:
                    details += 'FunctionPropertyState_Read'
                elif apcf_type == 9:
                    details += 'FunctionPropertyState_Response'
                elif 0xa <= apcf_type < 0x38:
                    details += 'USERMSG'
                elif 0x38 <= apcf_type < 0x3f:
                    details += 'Manufacturer specific USERMSG'
                elif apcf_type == 0x3f:
                    details += 'Reserved_0x3f'

            elif apcf_group == 0xc:
                details += 'DeviceDescriptor_Read'
            elif apcf_group == 0xd:
                details += 'DeviceDescriptor_Response'
            elif apcf_group == 0xe:
                details += 'Restart'

            else:
                if apcf_type <= 0x0f:
                    details += 'Coupler specific'
                elif apcf_type == 0x10:
                    details += 'MemoryBit_Write'

                elif apcf_type == 0x11:
                    details += 'Authorize_Request'
                elif apcf_type == 0x12:
                    details += 'Authorize_Response'
                elif apcf_type == 0x13:
                    details += 'Key_Write'
                elif apcf_type == 0x14:
                    details += 'Key_Response'

                elif apcf_type == 0x15:
                    details += 'PropertyValue_Read'
                elif apcf_type == 0x16:
                    details += 'PropertyValue_Response'
                elif apcf_type == 0x17:
                    details += 'PropertyValue_Write'
                elif apcf_type == 0x18:
                    details += 'PropertyDescr_Read'
                elif apcf_type == 0x19:
                    details += 'PropertyDescr_Response'

                elif apcf_type == 0x1a:
                    details += 'NetworkParam_Read'
                elif apcf_type == 0x1b:
                    details += 'NetworkParam_Response'

                elif apcf_type == 0x1c:
                    details += 'IndividualAddrSerialNumber_Read'
                elif apcf_type == 0x1d:
                    details += 'IndividualAddrSerialNumber_Response'
                elif apcf_type == 0x1e:
                    details += 'IndividualAddrSerialNumber_Write'

                elif apcf_type == 0x20:
                    details += 'DomainAddr_Write'
                elif apcf_type == 0x21:
                    details += 'DomainAddr_Read'
                elif apcf_type == 0x22:
                    details += 'DomainAddr_Response'
                elif apcf_type == 0x23:
                    details += 'DomainAddrSelective_Read'

                elif apcf_type == 0x24:
                    details += 'NetworkParam_Write'

                elif apcf_type == 0x25:
                    details += 'Link_Read'
                elif apcf_type == 0x26:
                    details += 'Link_Response'
                elif apcf_type == 0x27:
                    details += 'Link_Write'

                elif apcf_type == 0x28:
                    details += 'GroupPropValue_Read'
                elif apcf_type == 0x29:
                    details += 'GroupPropValue_Response'
                elif apcf_type == 0x2a:
                    details += 'GroupPropValue_Write'
                elif apcf_type == 0x2b:
                    details += 'GroupPropValue_InfoReport'

                elif apcf_type == 0x2c:
                    details += 'DomainAddrSerialNumber_Read'
                elif apcf_type == 0x2d:
                    details += 'DomainAddrSerialNumber_Response'
                elif apcf_type == 0x2e:
                    details += 'DomainAddrSerialNumber_Write'

                else:
                    details += 'ACPF_{0:x}'.format(apcf)

        details = details.strip()

        if use_seq:  # Add the transport sequence
            details += ' (S={0})'.format((telegram[6] >> 2) & 15)

        if data == '':
            if use_6bit_data:
                data = '%02x: ' % (telegram[7] & 0x3f)
            if len(telegram) > 8:
                data += ''.join(' %02x' % x for x in telegram[8:-1])

        if data != '':
            details += ': ' + data.strip()

        msg = '{0} to {1}: {2}'.format(from_addr, dest_addr, details)
        self.put(ss, es, self.out_ann, [self.rowid_label, [msg]])

    #
    # Get the data of a group value write/response as hex string
    #
    def telegram_group_value_data(self, telegram):
        if len(telegram) > 8:
            return '%x' % (telegram[7] & 0x3f)
        return '%x' % (telegram[7] & 0x3f) + ''.join(' %02x' % x for x in telegram[8:-1])
