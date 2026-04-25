import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct

class I2CSimulator:
    def __init__(self):
        # We will store the waveform as a series of (time, sda_state, scl_state)
        self.time = [0]
        self.sda = [1]
        self.scl = [1]
        self.current_t = 0
        
    def _step(self, sda_val, scl_val, duration=1):
        """Advances the simulation by 'duration' time steps."""
        self.current_t += duration
        self.time.append(self.current_t)
        self.sda.append(sda_val)
        self.scl.append(scl_val)

    def add_idle(self, duration=2):
        self._step(1, 1, duration)

    def add_start(self):
        # SCL is high, SDA goes low
        self._step(1, 1, 1)
        self._step(0, 1, 1)
        self._step(0, 0, 1)

    def add_stop(self):
        # SCL goes high, then SDA goes high
        self._step(0, 0, 1)
        self._step(0, 1, 1)
        self._step(1, 1, 1)
        self.add_idle()

    def add_bit(self, bit_val, stretch_duration=0):
        # Master sets data while SCL is low
        self._step(bit_val, 0, 1)
        
        if stretch_duration > 0:
            # CLOCK STRETCHING: Slave holds SCL low
            self._step(bit_val, 0, stretch_duration)
            
        # Clock goes high (data is valid)
        self._step(bit_val, 1, 2)
        # Clock goes low
        self._step(bit_val, 0, 1)

    def encode_byte(self, byte_val, is_nack=False, stretch_duration=0):
        """Encodes an 8-bit value MSB first, followed by ACK/NACK."""
        for i in range(7, -1, -1):
            bit = (byte_val >> i) & 1
            self.add_bit(bit)
            
        # 9th Bit: ACK (0) or NACK (1)
        ack_bit = 1 if is_nack else 0
        self.add_bit(ack_bit, stretch_duration=stretch_duration)

    def encode_packet(self, address, rw_bit, data_bytes, force_nack_at=-1, stretch_at=-1):
        """
        Encodes a full I2C packet.
        address: 7-bit integer
        rw_bit: 0 for Write, 1 for Read
        data_bytes: list of 8-bit integers
        force_nack_at: index of byte to NACK (-1 for no NACK)
        stretch_at: index of byte to apply clock stretching after (-1 for none)
        """
        self.add_start()
        
        # Address + R/W
        addr_byte = (address << 1) | (rw_bit & 1)
        self.encode_byte(addr_byte)
        
        for idx, data in enumerate(data_bytes):
            is_nack = (idx == force_nack_at)
            stretch = 5 if (idx == stretch_at) else 0
            self.encode_byte(data, is_nack=is_nack, stretch_duration=stretch)
            if is_nack:
                break # Master aborts on NACK
                
        self.add_stop()

    def decode_waveform(self):
        """Decodes the waveform arrays back into byte packets."""
        decoded_packets = []
        current_packet = []
        current_byte = 0
        bit_count = 0
        in_packet = False
        
        for i in range(1, len(self.time)):
            # Detect START: SCL is High, SDA falls
            if self.scl[i-1] == 1 and self.scl[i] == 1 and self.sda[i-1] == 1 and self.sda[i] == 0:
                in_packet = True
                current_packet = []
                current_byte = 0
                bit_count = 0
                continue
                
            # Detect STOP: SCL is High, SDA rises
            if self.scl[i-1] == 1 and self.scl[i] == 1 and self.sda[i-1] == 0 and self.sda[i] == 1:
                if in_packet:
                    decoded_packets.append(current_packet)
                in_packet = False
                continue
                
            # Sample Data: SCL rises
            if in_packet and self.scl[i-1] == 0 and self.scl[i] == 1:
                bit_val = self.sda[i]
                if bit_count < 8:
                    current_byte = (current_byte << 1) | bit_val
                    bit_count += 1
                else:
                    # 9th bit is ACK/NACK
                    ack_nack = "NACK" if bit_val == 1 else "ACK"
                    current_packet.append((hex(current_byte), ack_nack))
                    current_byte = 0
                    bit_count = 0
                    if bit_val == 1: # NACK usually aborts the sequence
                        pass 
                        
        return decoded_packets

def run_simulation():
    sim = I2CSimulator()
    
    # 1. Normal Packet (MPU6050 Addr 0x68, Write 0xAF)
    sim.encode_packet(address=0x68, rw_bit=0, data_bytes=[0xAF])
    
    # 2. Packet with Clock Stretching
    # Slave holds clock low after receiving 0x11
    sim.encode_packet(address=0x68, rw_bit=0, data_bytes=[0x11, 0x22], stretch_at=0)
    
    # 3. Packet with NACK
    # Master writes 0xEE, slave NACKs it, master stops
    sim.encode_packet(address=0x68, rw_bit=0, data_bytes=[0xEE, 0xFF], force_nack_at=0)

    # Decode what we generated
    decoded = sim.decode_waveform()
    print("--- I2C Decoder Output ---")
    for idx, pkt in enumerate(decoded):
        print(f"Packet {idx+1}: {pkt}")

    # Plotting & Animation
    fig, ax = plt.subplots(figsize=(12, 4))
    fig.canvas.manager.set_window_title('I2C Playground')
    
    ax.set_xlim(0, max(sim.time) + 5)
    ax.set_ylim(-0.5, 3.5)
    ax.set_yticks([0.5, 2.5])
    ax.set_yticklabels(['SDA', 'SCL'])
    ax.set_xlabel('Time (Simulation Ticks)')
    ax.set_title('I2C Protocol Simulation (Start, MSB-First, ACK/NACK, Clock Stretching)')
    ax.grid(True, which='both', axis='x', linestyle='--', alpha=0.5)

    # Offset SCL by +2 for visual stacking
    scl_plot_data = [val + 2 for val in sim.scl]
    
    line_sda, = ax.step([], [], where='post', color='blue', lw=2, label='SDA')
    line_scl, = ax.step([], [], where='post', color='red', lw=2, label='SCL')
    
    # Highlight stretches and NACKs
    ax.axvspan(65, 70, color='yellow', alpha=0.3, label='Clock Stretch')
    ax.axvspan(123, 125, color='red', alpha=0.2, label='NACK')
    ax.legend(loc='upper right')

    def init():
        line_sda.set_data([], [])
        line_scl.set_data([], [])
        return line_sda, line_scl

    def animate(i):
        # Speed up animation by revealing multiple steps per frame
        idx = min(i * 3, len(sim.time)) 
        line_sda.set_data(sim.time[:idx], sim.sda[:idx])
        line_scl.set_data(sim.time[:idx], scl_plot_data[:idx])
        return line_sda, line_scl

    # Frame count calculated to finish the whole array
    frames = (len(sim.time) // 3) + 10 
    ani = animation.FuncAnimation(fig, animate, init_func=init, frames=frames, interval=20, blit=True, repeat=False)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()