from io import TextIOWrapper
import os
import pwd
import time
from typing import Callable
from fake_serial import Serial

DEVICES: dict[str, dict[str, any]] = {
    'AT89S52': {'RAM': 2**8, 'ROM': 2**13},
    'AT89S51': {'RAM': 2**7, 'ROM': 2**12}
  } 

PROG_ENABLE = 'p' # returns
ERASE_CHIP  = 'e' # returns
ADDR_LSB    = 'a'
ADDR_MSB    = 'A'
CONTENT     = 'd'
RESET_HIGH  = 'o'
RESET_LOW   = 'c'
WRITE_PROG  = 'w'
READ_ID_LSB = 's' # returns 2 (?)
READ_ID_MSB = 'S' # returns   (?)
READ_PROG   = 'r' # returns



class Programmer:
  serial_port: str = ''
  port: Serial = object()

  file: TextIOWrapper = object()
  file_info = dict()
  file_contents: str = ''

  def setSerialPort(self, portname: str) -> bool:
    ''' Sets and checks destination SerialPort '''
    linux = portname.startswith("/dev/tty") or portname.startswith("/dev/pts")
    windows = portname.startswith("COM")
    if not windows and not linux:
      return False
      
    self.port = Serial(portname, 115200)
    self.serial_port = portname
    if not self.checkConnection():
      return False

    return True
    

  def setHexFile(self, file: TextIOWrapper) -> None:
    ''' Sets and checks source HexFile '''
    self.file = file
    self.file_info['path'] = os.path.abspath(file.name)
    self.file_contents = "".join(file.readlines()).replace(':', '').replace('\n', '')
    

  def checkConnection(self) -> bool:
    ''' Checks for compatible firmware on programmer device (Arduino) '''
    print("Warning: checkConnection() Not Implemented")
    return True

  def analyzeFile(self) -> dict[str, any]:
    ''' Extracts HexFile information '''
    modified = time.ctime(os.path.getmtime(self.file_info['path']))
    # size = os.stat(self.file_info['path']).st_size
    size = int(len(self.file_contents)/ 2) 
    owner = pwd.getpwuid(os.stat(self.file_info['path']).st_uid).pw_name
    self.file_info['name'] = self.file.name
    self.file_info['size'] = size
    self.file_info['modified'] = modified
    self.file_info['owner'] = owner
    return self.file_info

  def analyzeDevice(self) -> dict[str, any]:
    ''' Extracts Programmer Device (Arduino) and Target (AT89Sxx) information'''
    dev_info = dict()
    dev_info['port'] = self.serial_port
    dev_info['baudrate'] = self.port.baudrate
    model = "AT89S52"
    dev_info['device'] = model
    dev_info['RAM'] = DEVICES[model]['RAM']
    dev_info['ROM'] = DEVICES[model]['ROM']
    return dev_info
    
  def sendProgram(self, onUpdate: Callable[[float], None]) -> None:
    ''' Sends HexFile bytes to programmer for writing '''
    delay_ms = lambda ms: time.sleep(ms/1000)
    size = self.file_info['size']
    
    send = lambda byte: self.port.write(byte)

    send(RESET_HIGH)
    send(PROG_ENABLE)
    send(READ_ID_MSB)
    send(READ_ID_LSB)
    send(RESET_LOW)
    delay_ms(2)

    send(RESET_HIGH)
    send(PROG_ENABLE)
    send(ERASE_CHIP)
    send(RESET_LOW)
    delay_ms(500)

    send(RESET_HIGH)
    delay_ms(2)
    send(PROG_ENABLE)
    delay_ms(2)
    
    addr = 0
    for i in range(0, int(size*2), 2):
      data_str = self.file_contents[i:i+2]
      if data_str == '':
        continue
      data = int(data_str, base=16)      
      send(ADDR_LSB)
      send(addr & 0x00FF)
      delay_ms(10)

      send(ADDR_MSB)
      send((addr >> 8) & 0xFF00)
      delay_ms(10)

      send(CONTENT)
      send(data)
      delay_ms(10)

      send(WRITE_PROG)      
      addr += 1
      onUpdate(i/size)
      
    delay_ms(10)
    send(RESET_LOW)
    delay_ms(100)
