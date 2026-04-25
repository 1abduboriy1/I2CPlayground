# I2CPlayground 🛜

A complete Python-based simulation of the I2C (Inter-Integrated Circuit) protocol. This project builds the bridge between software logic and hardware realities, demonstrating how sensors (like the MPU6050 accelerometer) communicate with microcontrollers.

## 🚀 Features

* **MSB-First Encoding**: Converts hexadecimal sensor data into bit-level SDA/SCL representations.
* **Protocol Mechanics**: Accurate simulation of `START` and `STOP` conditions.
* **ACK / NACK Handling**: Simulates the crucial 9th bit where the slave acknowledges (LOW) or rejects (HIGH) a byte.
* **Clock Stretching**: Implements master-pause logic where the slave holds SCL LOW to process data before continuing.
* **Waveform Decoder**: A software parser that rebuilds the original bytes and ACKs directly from analyzing the rising/falling edges of the simulated SDA/SCL arrays.
* **Live Waveform Animation**: Uses `matplotlib` to render a step-plot animation of the serial clock and data lines in real-time.

## 🛠️ Tech Stack

* `Python 3.x`
* `matplotlib` (for live signal animation)
* `numpy` (for data structures and signal arrays)
* `struct` (for binary data packing/unpacking)

## ⚙️ Installation & Usage

1. **Install Dependencies:**
   ```bash
   pip install matplotlib numpy