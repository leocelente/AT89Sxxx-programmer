from io import TextIOWrapper
import os
import pwd
import time
from typing import Callable
from serial import Serial
from intelhex import IntelHex

TARGETS: dict[str, dict[str, any]] = {
    'AT89S52': {'RAM': 2**8, 'ROM': 2**13},
    'AT89S51': {'RAM': 2**7, 'ROM': 2**12},
    'AT89S8253': {'RAM': 2**8, 'ROM': 12288 }
  }
# Commands to Arduino
PROG_ENABLE = 'p'.encode('utf-8') # returns
ERASE_CHIP  = 'e'.encode('utf-8') # returns
ADDR_LSB    = 'a'.encode('utf-8')
ADDR_MSB    = 'A'.encode('utf-8')
CONTENT     = 'd'.encode('utf-8')
RESET_HIGH  = 'o'.encode('utf-8')
RESET_LOW   = 'c'.encode('utf-8')
WRITE_PROG  = 'w'.encode('utf-8')
READ_ID_LSB = 's'.encode('utf-8') # returns 2 (?)
READ_ID_MSB = 'S'.encode('utf-8') # returns   (?)
READ_PROG   = 'r'.encode('utf-8') # returns

class Programmer:
  serial_port: str = ''
  port: Serial = object()

  file: TextIOWrapper = object()
  file_info = dict()
  file_contents: str = ''
  
  target: str = ''

  ih = IntelHex()


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
    self.ih.fromfile(file.name, format='hex')
    

  def checkConnection(self) -> bool:
    ''' Checks for compatible firmware on programmer device (Arduino) '''
    print("[!] - Warning: checkConnection() Not Implemented")
    return True

  def analyzeFile(self) -> dict[str, any]:
    ''' Extracts HexFile information '''
    modified = time.ctime(os.path.getmtime(self.file_info['path']))
    # size = os.stat(self.file_info['path']).st_size
    # size = int(len(self.file_contents)/ 2) 
    size = len(self.ih.tobinarray())
    owner = pwd.getpwuid(os.stat(self.file_info['path']).st_uid).pw_name
    self.file_info['name'] = self.file.name.split('/')[-1]
    self.file_info['size'] = size
    self.file_info['modified'] = modified
    self.file_info['owner'] = owner
    return self.file_info

  def analyzeDevice(self, target: str) -> dict[str, any]:
    ''' Extracts Programmer Device (Arduino) and Target (AT89Sxx) information'''
    self.target = target
    dev_info = dict()
    dev_info['port'] = self.serial_port
    dev_info['baudrate'] = self.port.baudrate
    model = self.target
    dev_info['device'] = model
    dev_info['RAM'] = TARGETS[model]['RAM']
    dev_info['ROM'] = TARGETS[model]['ROM']
    return dev_info
    
  def sendProgram(self, onUpdate: Callable[[float], None]) -> None:
    ''' Sends HexFile bytes to programmer for writing '''
    delay_ms = lambda ms: time.sleep(ms/1000)
    size = self.file_info['size']
    
    def send(byte: int):
       self.port.write(byte)
       delay_ms(1)

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
    
    program = self.ih.todict()
    for i, (addr, data) in enumerate(program.items()):
      send(ADDR_LSB)
      lsb = (addr & 0x00FF) 
      send(lsb.to_bytes(1, 'little'))
      delay_ms(10)

      send(ADDR_MSB)
      hsb = (addr & 0xFF00) >> 8
      send(hsb.to_bytes(1, 'little'))
      delay_ms(10)

      send(CONTENT)
      send(data.to_bytes(1, 'little'))
      delay_ms(10)

      send(WRITE_PROG)      
      onUpdate(i/size)
      
    delay_ms(10)
    send(RESET_LOW)
    delay_ms(100)

  def close(self):
    self.port.close()
