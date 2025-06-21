from pymem.ptypes import RemotePointer
from SqlControl import SqlControl
from send_msg import send_danmu
import threading
from pymem import Pymem
import pymem.pattern
import ctypes
from ctypes import wintypes
import time
import pymem
import json
class PvzCheat:
    def __init__(self):
        self.pm = Pymem("PlantsVsZombiesRH.exe")
        self.offset_list = [0x000000B8,0,0x000000CC] 
        self.GameAssembly_dll = self.getModuleAddr("GameAssembly.dll")
        self.sun_base_address = self.GameAssembly_dll+0x1C99770
        self.speedx_base_address = self.GameAssembly_dll+0x1C67168
        self.sun_address = self.getPointerAddress(self.offset_list,self.sun_base_address) 

        # 判断左键点击
        self.mouse_click_in_address = self.GameAssembly_dll+0x3B3A2D
        # 判断右键点击
        self.mouse_right_in_address = self.GameAssembly_dll+0x3B3B55
        # 原程序记录赢的那条路
        self.win_in_address = self.GameAssembly_dll+0x436377
        # 访问了坐标的代码
        self.get_position_address = self.getModuleAddr("UnityPlayer.dll")+0xA1073E
        # 点击主菜单类的判断
        self.click_menu_address = self.GameAssembly_dll+0x141C208
        # 执行ESC的地址
        self.esc_address = self.GameAssembly_dll+0x300884 
        # 倍速设置
        self.speed_address = self.getPointerAddress([0xB8,0xF8],self.speedx_base_address)

        self.click_address = None
        self.click_address_1 = None
        self.right_click_address = None
        self.is_win_address = None
        self.win_road_num_address = None
        # 定义存储坐标地址
        self.position_address = None
        # 点击ESC
        self.click_esc_address = None

        with open("data/mouse_positions.json", "r", encoding="utf-8") as file:
            self.game_map = json.loads(file.read())
        with open("data/zhi_wu.json", "r", encoding="utf-8") as file:
            self.zhi_wu = json.loads(file.read())
        with open("data/tools.json", "r", encoding="utf-8") as file:
            self.tools = json.loads(file.read())
        with open("data/cost.json","r",encoding="utf-8") as file:
            self.cost = json.load(file)
        with open("data/select_to_board.json","r",encoding="utf-8") as file:
            self.select_to_board = json.load(file)

        self.blive_usr = SqlControl()
        self.allocate_members = []
        self.data_address = None
        self.inject()
        threading.Thread(target=self.freeze_sun,daemon = True).start()

    def allocate_memory(self,size,original_address):
        # 定义 VirtualAllocEx 函数
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        VirtualAllocEx = kernel32.VirtualAllocEx
        VirtualAllocEx.restype = wintypes.LPVOID
        VirtualAllocEx.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]

        mask = ~0xFFFF
        # border_address = ((original_address - 0x80000000) & mask)+0x10000
        original_address = (original_address & mask)
        start_address = 0
        for i in range(original_address,original_address+0x7FFFFFFF,0x10000):
            exist = 0
            value = 0
            try:
                value = self.pm.read_int(i)
                exist = 1
            except:
                pass
            if exist == 0:
                start_address = i
                break
        if start_address == 0:
            return None
        # 定义常量
        MEM_COMMIT = 0x1000
        MEM_RESERVE = 0x2000
        PAGE_EXECUTE_READWRITE = 0x40

        allocated_memory = VirtualAllocEx(self.pm.process_handle, start_address, size, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
        return allocated_memory

    def test(self):
        print(hex(self.click_address))

    # 寻找目标注入地址
    def calculate_target_address(self,current_address):
        # print(hex(self.pm.read_ulonglong(current_address)))
        offset_hex = hex(self.pm.read_ulonglong(current_address))[-10:-2]
        # print(offset_hex)
        offset = int(offset_hex, 16)

        if offset > 0x7FFFFFFF:
            offset -= 0x100000000  # 将其转换为负数

        # 操作码 E9 占 5 个字节的指令长度
        instruction_length = 5
        target_address = current_address + instruction_length + offset
        return target_address

    def getModuleAddr(self,dllName):
        global ModuleAddr
        modules = list(self.pm.list_modules())
        for module in modules:
            if module.name == dllName:
                ModuleAddr = module.lpBaseOfDll
        return ModuleAddr

    def getPointerAddress(self,offsets,base_address):
        remote_pointer = RemotePointer(self.pm.process_handle, base_address)
        for offset in offsets:
            if offset != offsets[-1]:
                remote_pointer = RemotePointer(self.pm.process_handle, remote_pointer.value + offset)
            else:
                return remote_pointer.value + offset

    def get_sun(self):
        self.sun_address = self.getPointerAddress(self.offset_list,self.sun_base_address)
        return self.pm.read_int(self.sun_address)

    def change_sun(self,sun_value):
        try:
            self.sun_address = self.getPointerAddress(self.offset_list,self.sun_base_address)
        except:
            time.sleep(1)
            return
        self.pm.write_int(self.sun_address, sun_value)
    def freeze_sun(self):
        while True:
            self.change_sun(100000)
            time.sleep(1)
            
    def change_position(self,x,y):
        hex_string = "0x"+hex(y)[2:].zfill(8)+hex(x)[2:].zfill(8)
        # print(hex_string)
        number = int(hex_string,16)
        self.pm.write_longlong(self.position_address,number)

    def mouse_click(self,x,y):
        # time.sleep(0.05)
        self.change_position(x,y)
        time.sleep(0.002)
        self.pm.write_int(self.click_address,1)
        self.pm.write_int(self.click_address_1,1)
        time.sleep(0.01)
        # self.pm.write_int(self.click_address_1,8)

    
    def plant_plants(self,plant_word:str,position:str):
        if plant_word in self.zhi_wu and position in self.game_map:
            # time.sleep(0.1)
            zhi_wu_x,zhi_wu_y = self.zhi_wu[plant_word][0],self.zhi_wu[plant_word][1]
            self.mouse_click(zhi_wu_x,zhi_wu_y)
            # time.sleep(0.1)
            map_x,map_y = self.game_map[position][0],self.game_map[position][1]
            self.mouse_click(map_x,map_y)
            # time.sleep(0.1)
            self.pm.write_int(self.right_click_address,1)
            time.sleep(0.01)
            self.pm.write_longlong(self.position_address, 0)
            # time.sleep(0.1)
            return True
        else:
            return False
    def shovel_plants(self,position:str):

        chan_x,chan_y = self.tools["shovel"][0],self.tools["shovel"][1]
        # time.sleep(0.1)
        self.mouse_click(chan_x,chan_y)
        # time.sleep(0.05)
        map_x,map_y = self.game_map[position][0],self.game_map[position][1]
        self.mouse_click(map_x,map_y)
        # time.sleep(0.005)
        # self.plant_plants("n",position)


    def get_win_road(self):
        status = self.pm.read_int(self.is_win_address)
        if status == 1:
            road_num = self.pm.read_int(self.win_road_num_address)
            self.pm.write_int(self.is_win_address,0)
            return road_num+1
        else:
            return -1
            
    def show_shovel(self):
        print("显示铲子")
        x,y = self.tools["show_shovel"][0],self.tools["show_shovel"][1]
        time.sleep(0.1)
        self.change_position(x,y)
        time.sleep(0.1)
        # print(hex(self.click_address_1))
        self.pm.write_int(self.click_address_1,1)
        time.sleep(0.1)
        self.pm.write_longlong(self.position_address, 0)
        time.sleep(0.1)

    def push_esc(self):
        self.mouse_click(self.tools["set_zombie"][0],self.tools["set_zombie"][1])
        time.sleep(0.1)
        self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])
        self.pm.write_longlong(self.position_address, 0)

    def change_speed(self,speed):
        speed = float(speed)
        self.pm.write_float(self.speed_address,speed)
        self.pm.write_int(self.click_esc_address,2)

    def calculate_offset(self,original_address,target_address,code_length):
        relative_offset = target_address - (original_address + code_length)
        if not -0x80000000 <= relative_offset <= 0x7FFFFFFF:
            raise ValueError("Relative offset is out of 32-bit range")
        return relative_offset.to_bytes(4,byteorder="little",signed=True)

    def select_zp_to_board(self):
        keys = list(self.select_to_board.keys())
        self.mouse_click(self.tools["set_zombie"][0],self.tools["set_zombie"][1])
        time.sleep(0.1)
        for key in self.select_to_board:
            x,y = self.select_to_board[key][0],self.select_to_board[key][1]
            if key != keys[-1]:
                self.mouse_click(x,y)
            else:
                self.mouse_click(self.tools["set_zombie"][0],self.tools["set_zombie"][1])
                time.sleep(0.1)
                self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])
                time.sleep(0.1)
                self.mouse_click(x,y)
        time.sleep(0.2)
        self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])
        self.pm.write_longlong(self.position_address, 0)



    def inject(self):
        # 注入汇编代码，左键点击控制
        original_address = self.mouse_click_in_address
        address = self.allocate_memory(4096, original_address)
        free_address = address
        self.data_address = address + 0x800

        self.allocate_members.append({
            "name":"left_mouse_click",
            "original_code":self.pm.read_bytes(original_address,15),
            "original_address":original_address,
            "free_address":free_address
        })

        print("申请地址：",hex(address))

        GameAssembly_dll_3B3AEC = self.GameAssembly_dll+0x3B3AEC
        GameAssembly_dll_1DACE6B = self.GameAssembly_dll+0x1DACE6B

        self.click_address = self.data_address
        assembly_code = (
            b'\x3C\x01'+  # cmp al,01                     
            bytes.fromhex("0F 84 11 00 00 00")+ # je 0x11
            b'\x48\x8B\x05'+self.calculate_offset(address+8,self.click_address,7)+ # mov rax,[data_address]
            b'\xC7\x05'+self.calculate_offset(address+15,self.click_address,10)+bytes.fromhex("00 00 00 00")+# mov [data_address],00000000
            b'\x84\xC0'+ # test al,al
            b'\x0F\x84'+self.calculate_offset(address+27,GameAssembly_dll_3B3AEC,6)+ # je GameAssembly.dll+3CD6F8
            b'\x80\x3D'+self.calculate_offset(address+33,GameAssembly_dll_1DACE6B,7)+b'\x00'+ # cmp byte ptr [GameAssembly.dll+1C9F552],00
            b'\xE9' + self.calculate_offset(address+40,original_address+15,5)  # jmp return
        )
        # 写入到新申请的内存
        self.pm.write_bytes(address,assembly_code,len(assembly_code))

        fill_original_code = (
            b'\xE9'+self.calculate_offset(original_address,address,5)+  # jmp [address]
            bytes.fromhex("66 0F 1F 44 00 00")   #nop word ptr [rax+rax+00]
        )   
        
        # 写入跳转到新内存
        self.pm.write_bytes(original_address,fill_original_code,len(fill_original_code))
        
        # 代码注入，右键点击控制
        address += len(assembly_code) +4 
        original_address = self.mouse_right_in_address
        self.allocate_members.append({
            "name":"right_mouse_click",
            "original_code":self.pm.read_bytes(original_address,6),
            "original_address":original_address,
        })

        # 操控右键点击的状态
        self.right_click_address = self.data_address+16

        GameAssembly_dll_3B3B63 = self.GameAssembly_dll+0x3B3B63


        assembly_code = (
            b'\x3C\x01'+  # cmp al,01                     
            bytes.fromhex("0F 84 07 00 00 00")+ # je 0x11
            b'\x48\x8B\x05'+self.calculate_offset(address+8,self.right_click_address,7)+ # mov rax,[right_click_address]
            b'\xC7\x05'+self.calculate_offset(address+15,self.right_click_address,10)+bytes.fromhex("00 00 00 00")+# mov [right_click_address],00000000
            b'\x84\xC0'+ # test al,al
            b'\x0F\x84'+self.calculate_offset(address+27,GameAssembly_dll_3B3B63,6)+ # je GameAssembly.dll+3CD712
            b'\x31\xD2' # xor edx,edx
            b'\xE9' + self.calculate_offset(address+35,original_address+6,5)  # jmp return
        )
        # 写入到新申请的内存
        self.pm.write_bytes(address,assembly_code,len(assembly_code))

        fill_original_code = (
            b'\xE9'+self.calculate_offset(original_address,address,5)+  # jmp [address]
            b'\x90'   # nop
        )   
        # 写入跳转到新内存
        self.pm.write_bytes(original_address,fill_original_code,len(fill_original_code))

        # 代码注入，获取赢的那条路
        
        address += len(assembly_code) +4
        original_address = self.win_in_address
        self.allocate_members.append({
            "name":"win_road",
            "original_code":self.pm.read_bytes(original_address,7),
            "original_address":original_address,
        })
        
        # 此状态为是否有路赢了。
        self.is_win_address = self.data_address + 32
        # 记录赢的那一条路
        self.win_road_num_address = self.data_address + 36

        assembly_code = (
            b'\x89\x48\x30'+ # mov [rax+30],ecx
            b'\xC7\x05'+ self.calculate_offset(address+3,self.is_win_address,10) + bytes.fromhex("01 00 00 00")+ # mov [is_win_address],1
            b'\x89\x0D'+ self.calculate_offset(address+13,self.win_road_num_address,6)+ # mov [win_road_num_address],ecx
            bytes.fromhex("48 8B 53 28")+ # mov rdx,[rbx+28]
            b'\xE9' + self.calculate_offset(address+23,original_address+7,5) # jmp return
        )
        # 写入到新申请的内存
        self.pm.write_bytes(address,assembly_code,len(assembly_code))

        fill_original_code = (
            b'\xE9'+self.calculate_offset(original_address,address,5)+  # jmp [address]
            b'\x66\x90'   # nop 2
        )   
        # 写入跳转到新内存
        self.pm.write_bytes(original_address,fill_original_code,len(fill_original_code))
        

        # 注入代码，改变坐标
        address += len(assembly_code) +4
        original_address = self.get_position_address
        self.allocate_members.append({
            "name":"change_position",
            "original_code":self.pm.read_bytes(original_address,7),
            "original_address":original_address,
        })
        
        # 存储要修改的地址
        self.position_address = self.data_address + 52

        assembly_code=(
            b'\x48\x8B\x15' + self.calculate_offset(address,self.position_address,7)+ # mov rdx,[position_address]
            bytes.fromhex("48 83 FA 00")+ # cmp rdx,00
            bytes.fromhex("0F 85 04 00 00 00")+ # jne 0x4
            bytes.fromhex("48 8B 55 70")+ # mov rdx,[rbp+70]
            bytes.fromhex("45 31 C0") + # xor r8d,r8d
            b'\xE9'+ self.calculate_offset(address+24,original_address+7,5) # jmp return
        )
        # 写入到新申请的内存
        self.pm.write_bytes(address,assembly_code,len(assembly_code))

        fill_original_code = (
            b'\xE9'+self.calculate_offset(original_address,address,5)+  # jmp [address]
            b'\x66\x90'   # nop 2
        )   
        # 写入跳转到新内存
        self.pm.write_bytes(original_address,fill_original_code,len(fill_original_code))

        # 注入代码，为了点击主菜单那些
        address += len(assembly_code) +4
        original_address = self.click_menu_address
        self.allocate_members.append({
            "name":"click_menu",
            "original_code":self.pm.read_bytes(original_address,9),
            "original_address":original_address,
        })

        # 左键点击状态
        self.click_address_1 = self.data_address+68

        GameAssembly_dll_1C7ED88 = self.GameAssembly_dll + 0x1C7ED88


        assembly_code=(
            b'\xFF\xD0'+ # call rax
            bytes.fromhex("48 83 F8 01")+ # cmp rax,01
            bytes.fromhex("0F 84 11 00 00 00")+ # je 0x11
            b'\x48\x8B\x05' + self.calculate_offset(address+12,self.click_address_1,7)+ # mov rdx,[click_address]
            bytes.fromhex("C7 05")+ self.calculate_offset(address+19,self.click_address_1,10)+bytes.fromhex("00 00 00 00")+ # mov [click_address],00000000
            b'\x48\x8B\x0D' + self.calculate_offset(address+29,GameAssembly_dll_1C7ED88,7)+ # mov rcx,[GameAssembly.dll+1B723D0]
            b'\xE9'+ self.calculate_offset(address+36,original_address+9,5) # jmp return
        )

        # 写入到新申请的内存
        self.pm.write_bytes(address,assembly_code,len(assembly_code))

        fill_original_code = (
            b'\xE9'+self.calculate_offset(original_address,address,5)+  # jmp [address]
            bytes.fromhex("0F 1F 40 00") # nop dword ptr [rax+00]
        )   
        # 写入跳转到新内存
        self.pm.write_bytes(original_address,fill_original_code,len(fill_original_code))

        # 注入代码，点击ESC
        address += len(assembly_code) +4
        original_address = self.esc_address
        self.allocate_members.append({
            "name":"click_esc",
            "original_code":self.pm.read_bytes(original_address,6),
            "original_address":original_address,
        })

        # 点击ESC状态
        self.click_esc_address = self.data_address+84
        GameAssembly_dll_300898 = self.GameAssembly_dll + 0x300898


        assembly_code=(
            b'\x83\x3D'+ self.calculate_offset(address,self.click_esc_address,7)+b'\x00'+ # cmp dword ptr [click_esc_address],00
            bytes.fromhex("0F 84 11 00 00 00")+ # je 0x11
            b'\x8B\x1D'+ self.calculate_offset(address+13,self.click_esc_address,6)+ # mov ebx,[click_esc_address]
            b'\x83\xEB\x01'+ # sub ebx,01
            b'\x89\x1D'+ self.calculate_offset(address+22,self.click_esc_address,6) + # mov [click_esc_address],ebx
            b'\xB0\x01'+ # mov al,01
            b'\x84\xC0'+ # test al,al
            b'\x0F\x85'+self.calculate_offset(address+32,GameAssembly_dll_300898,6)+ # jne GameAssembly.dll+301921
            b'\x31\xD2' # xor edx,edx
            b'\xE9'+ self.calculate_offset(address+40,original_address+6,5) # jmp return
        )

        # 写入到新申请的内存
        self.pm.write_bytes(address,assembly_code,len(assembly_code))

        fill_original_code = (
            b'\xE9'+self.calculate_offset(original_address,address,5)+  # jmp [address]
            b'\x90' # nop
        )
        # 写入跳转到新内存
        self.pm.write_bytes(original_address,fill_original_code,len(fill_original_code))
        


    def __enter__(self):
        print("cheat enter")

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("释放资源")
        for value in self.allocate_members:
            if "original_address" in value:
                self.pm.write_bytes(value["original_address"],value["original_code"],len(value["original_code"]))
        for value in self.allocate_members:
            if "free_address" in value:
                self.pm.free(value["free_address"])

if __name__ == "__main__":
    pvzcheat = PvzCheat()
    # with pvzcheat:
        # pvzcheat.change_sun(100000)
    with pvzcheat:
        while True:
            a = input("输入：")
            if a == "1":
                for i in range(1,11):
                    pvzcheat.shovel_plants(str(i))
            elif a == "2":
                for i in range(1,11):
                    pvzcheat.plant_plants("h",str(i))
            elif a == "3":
                pvzcheat.show_shovel()
            elif a == "4":
                pvzcheat.pm.write_int(pvzcheat.click_address_1,1)
            elif a == "5":
                pvzcheat.shovel_plants("1")
            elif a == "6":
                b = input("输入倍速：")
                pvzcheat.change_speed(b)
            elif a == "7":
                print(pvzcheat.get_win_road())
            elif a == "8":
                pvzcheat.select_zp_to_board()
            elif a == "9":
                pvzcheat.push_esc()
            else:
                zhi_wu_x,zhi_wu_y = pvzcheat.zhi_wu["h"][0],pvzcheat.zhi_wu["h"][1]
                pvzcheat.mouse_click(zhi_wu_x,zhi_wu_y)
                time.sleep(float(a))
                map_x,map_y = pvzcheat.game_map["1"][0],pvzcheat.game_map["1"][1]
                pvzcheat.mouse_click(map_x,map_y)

    