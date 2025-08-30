from pymem.ptypes import RemotePointer
import win32api
import win32con
import win32gui
import win32process
import threading
from pymem import Pymem

import ctypes
from ctypes import wintypes
import time
import pymem
import json

class PvzCheat:

    def __init__(self):
        self.pm = Pymem("PlantsVsZombiesRH.exe")
        self.offset_list = [0x000000B8,0,0x000000E0] 
        self.GameAssembly_dll = self.getModuleAddr("GameAssembly.dll")
        self.UnityPlayer_dll = self.getModuleAddr("UnityPlayer.dll")

        self.sun_base_address = self.GameAssembly_dll+0x1E3E988
        self.speedx_base_address = self.GameAssembly_dll+0x1E4C800

        # 判断左键点击
        self.mouse_click_in_address = self.GameAssembly_dll+0x475A1D
        # 判断右键点击
        self.mouse_right_in_address = self.GameAssembly_dll+0x475B40    
        # 点击主菜单类的判断
        self.click_menu_address = self.GameAssembly_dll+0x1592CA8
        # 访问了坐标的代码
        self.get_position_address = self.UnityPlayer_dll+0xA1073E
        # 执行ESC的地址
        self.esc_address = self.GameAssembly_dll+0x316488 
        # 原程序记录赢的那条路
        self.win_in_address = self.GameAssembly_dll+0x4FF246
        # 倍速设置
        # self.speed_address = self.getPointerAddress([0xB8,0xE8],self.speedx_base_address)
        # 指定放置植物
        self.select_plants_address = self.GameAssembly_dll + 0x469C47
        # 指定放置僵尸
        self.select_zombie_address = self.GameAssembly_dll + 0x4699F1
        self.click_address = None
        self.click_address_1 = None
        self.right_click_address = None
        self.is_win_address = None
        self.win_road_num_address = None
        # 定义存储坐标地址
        self.position_address = None
        # 点击ESC
        self.click_esc_address = None
        # 存放植物id的数据地址
        self.plantid_address = None
        # 存放僵尸id的数据地址
        self.zombieid_address = None

        self.game_map = None
        self.zhi_wu = None
        self.tools = None
        self.cost = None
        self.select_to_board = None

        self.allocate_members = []
        self.data_address = None

    def get_hwnd(self):
        hwnds = []
        def enum_windows_callback(hwnd, hwnds):
            tid, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == self.pm.process_id:
                hwnds.append(hwnd)
        win32gui.EnumWindows(enum_windows_callback, hwnds)
        return hwnds[0] if hwnds else None

    def load_data(self):
        left, top, right, bottom = win32gui.GetWindowRect(self.get_hwnd())
        with open("data/mouse_positions.json", "r", encoding="utf-8") as file:
            position_info = json.load(file)
        map_position = position_info[0]
        x_offset = (map_position["10"][0]-map_position["1"][0]) //9
        x_coordinates = []
        for i in range(10):
            x_coordinates.append(map_position["1"][0]+i*x_offset)
        y_offset = (map_position["41"][1]-map_position["1"][1]) // 4
        y_coordinates = []
        for i in range(5):
            y_coordinates.append(map_position["1"][1]+i*y_offset)
        self.game_map = {}
        index_num = 1
        for y in y_coordinates:
            for x in x_coordinates:
                self.game_map[str(index_num)] = [x-left,y-top]
                index_num+=1
        # with open("data/zhi_wu.json", "r", encoding="utf-8") as file:
        #     self.zhi_wu = json.loads(file.read())
        select_pos = position_info[1]
        x_offset = (select_pos["14"][0]-select_pos["1"][0]) //13
        x_coordinates = []
        for i in range(13):
            x_coordinates.append(select_pos["1"][0]+i*x_offset)
        self.zhi_wu = {}
        index_num = 1
        for x in x_coordinates:
            self.zhi_wu[str(index_num)] = [x-left,select_pos["1"][1]-top]
            index_num+=1
        with open("data/tools.json", "r", encoding="utf-8") as file:
            self.tools = json.loads(file.read())
        for key in self.tools:
            self.tools[key] = [self.tools[key][0]-left,self.tools[key][1]-top]
        with open("data/cost.json","r",encoding="utf-8") as file:
            self.cost = json.load(file)
        with open("data/select_to_board.json","r",encoding="utf-8") as file:
            self.select_to_board = json.load(file)
        for key in self.select_to_board:
            self.select_to_board[key] = [self.select_to_board[key][0]-left,self.select_to_board[key][1]-top]


    def calculate_offset(self,original_address,target_address,code_length):
        relative_offset = target_address - (original_address + code_length)
        if not -0x80000000 <= relative_offset <= 0x7FFFFFFF:
            raise ValueError("Relative offset is out of 32-bit range")
        return relative_offset.to_bytes(4,byteorder="little",signed=True)
    
    def calculate_target_address(self,original_address, relative_offset, code_length):
        """
        通过原地址和相对偏移量计算目标地址

        original_address: int，原地址
        relative_offset: bytes，偏移量
        code_length: int，代码长度
        返回目标地址（int）
        """
        relative_offset = int.from_bytes(relative_offset, byteorder='little', signed=True)
        target_address = original_address + code_length + relative_offset
        return target_address

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
        time.sleep(0.003)
        self.pm.write_int(self.click_address,1)
        self.pm.write_int(self.click_address_1,1)
        time.sleep(0.02)
        # self.pm.write_int(self.click_address_1,8)

    def click_positoin(self,position:str):
        if position in self.game_map:
            map_x,map_y = self.game_map[position][0],self.game_map[position][1]
            self.mouse_click(map_x,map_y)
    
    def plant_plants(self,plantid:int,position:str):
        self.pm.write_int(self.plantid_address,plantid)
        self.change_sun(100000)
        plant_word = "2"
        if position in self.game_map:
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
    
    def plant_zombie(self,zombieid:int,position:str):
        self.pm.write_int(self.zombieid_address,zombieid)
        plant_word = "1"
        if position in self.game_map:
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

    def put_esc(self):
        self.pm.write_int(self.click_esc_address,1)

    def change_speed(self,speed):
        speed = float(speed)
        self.pm.write_float(self.speed_address,speed)
        self.pm.write_int(self.click_esc_address,2)

    def click_random_plant(self):
        self.mouse_click(self.tools["random_plants"][0],self.tools["random_plants"][1])

    def select_zp_to_board(self):
        # keys = list(self.select_to_board.keys())
        self.mouse_click(self.tools["set_zombie"][0],self.tools["set_zombie"][1])
        x,y = self.select_to_board["1"][0],self.select_to_board["1"][1]
        time.sleep(0.01)
        self.mouse_click(x,y)
        time.sleep(0.01)
        self.mouse_click(self.tools["set_zombie"][0],self.tools["set_zombie"][1])
        time.sleep(0.01)
        self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])
        time.sleep(0.01)
        self.mouse_click(x,y)
        time.sleep(0.01)
        self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])
        self.pm.write_longlong(self.position_address, 0)

    def pressure_test(self,n):
        for i in range(n):
            self.mouse_click(self.tools["set_zombie"][0],self.tools["set_zombie"][1])
            self.mouse_click(self.tools["set_zombie"][0],self.tools["set_zombie"][1])
            self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])
            self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])
            # self.pm.write_longlong(self.position_address, 0)

    def stuck(self):
        self.mouse_click(self.tools["set_zombie"][0],self.tools["set_zombie"][1])
        self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])

    def move_plants(self,start_pos,end_pos):
        if start_pos in self.game_map and end_pos in self.game_map:
            self.mouse_click(self.tools["glove"][0],self.tools["glove"][1])
            x,y = self.game_map[start_pos][0],self.game_map[start_pos][1]
            self.mouse_click(x,y)
            x,y = self.game_map[end_pos][0],self.game_map[end_pos][1]
            self.mouse_click(x,y)
            self.pm.write_int(self.right_click_address,1)
            time.sleep(0.01)
            self.pm.write_longlong(self.position_address, 0)


    def inject(self):
        # 注入汇编代码，左键点击控制=======================================
        original_address = self.mouse_click_in_address
        original_code = self.pm.read_bytes(original_address,15)
        address = self.allocate_memory(4096, original_address)
        free_address = address
        self.data_address = address + 0x800

        self.allocate_members.append({
            "name":"left_mouse_click",
            "original_code":original_code,
            "original_address":original_address,
            "free_address":free_address
        })

        print("申请地址：",hex(address))

        # GameAssembly_dll_3F0FFC = self.GameAssembly_dll+0x3F0FFC
        offset_bytes = original_code[4:8]  
        GameAssembly_dll_3F0FFC = self.calculate_target_address(original_address+2,offset_bytes,6)

        # GameAssembly_dll_1EAC9C7 = self.GameAssembly_dll+0x1EAC9C7
        offset_bytes = original_code[10:14]  
        GameAssembly_dll_1EAC9C7 = self.calculate_target_address(original_address+8,offset_bytes,7)


        self.click_address = self.data_address
        assembly_code = (
            b'\x3C\x01'+  # cmp al,01                     
            bytes.fromhex("0F 84 11 00 00 00")+ # je 0x11
            b'\x48\x8B\x05'+self.calculate_offset(address+8,self.click_address,7)+ # mov rax,[data_address]
            b'\xC7\x05'+self.calculate_offset(address+15,self.click_address,10)+bytes.fromhex("00 00 00 00")+# mov [data_address],00000000
            b'\x84\xC0'+ # test al,al
            b'\x0F\x84'+self.calculate_offset(address+27,GameAssembly_dll_3F0FFC,6)+ # je GameAssembly.dll+3CD6F8
            b'\x80\x3D'+self.calculate_offset(address+33,GameAssembly_dll_1EAC9C7,7)+b'\x00'+ # cmp byte ptr [GameAssembly.dll+1C9F552],00
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
        
        # 代码注入，右键点击控制=======================================================================
        address += len(assembly_code) +4 
        original_address = self.mouse_right_in_address
        original_code = self.pm.read_bytes(original_address,6)
        self.allocate_members.append({
            "name":"right_mouse_click",
            "original_code":original_code,
            "original_address":original_address,
        })

        # 操控右键点击的状态
        self.right_click_address = self.data_address+16

        GameAssembly_dll_3F1073 = self.calculate_target_address(original_address+2,original_code[3:4],2)
        # print(GameAssembly_dll_3F1073)
        # GameAssembly_dll_3F1073 = self.GameAssembly_dll+0x3F1073
        # print(GameAssembly_dll_3F1073)

        assembly_code = (
            b'\x3C\x01'+  # cmp al,01                     
            bytes.fromhex("0F 84 07 00 00 00")+ # je 0x11
            b'\x48\x8B\x05'+self.calculate_offset(address+8,self.right_click_address,7)+ # mov rax,[right_click_address]
            b'\xC7\x05'+self.calculate_offset(address+15,self.right_click_address,10)+bytes.fromhex("00 00 00 00")+# mov [right_click_address],00000000
            b'\x84\xC0'+ # test al,al
            b'\x0F\x84'+self.calculate_offset(address+27,GameAssembly_dll_3F1073,6)+ # je GameAssembly.dll+3CD712
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

        # 代码注入，获取赢的那条路========================================================================
        
        address += len(assembly_code) +4
        original_address = self.win_in_address
        self.allocate_members.append({
            "name":"win_road",
            "original_code":self.pm.read_bytes(original_address,5),
            "original_address":original_address,
        })
        
        # 此状态为是否有路赢了。
        self.is_win_address = self.data_address + 32
        # 记录赢的那一条路
        self.win_road_num_address = self.data_address + 36

        assembly_code = (
            bytes.fromhex("8B 40 20")+ # mov eax,[rax+20]
            b'\xC7\x05'+ self.calculate_offset(address+3,self.is_win_address,10) + bytes.fromhex("01 00 00 00")+ # mov [is_win_address],1
            b'\x89\x05'+ self.calculate_offset(address+13,self.win_road_num_address,6)+ # mov [win_road_num_address],eax
            bytes.fromhex("33 D2")+ # xor edx,edx
            b'\xE9' + self.calculate_offset(address+21,original_address+5,5) # jmp return
        )
        # 写入到新申请的内存
        self.pm.write_bytes(address,assembly_code,len(assembly_code))

        fill_original_code = (
            b'\xE9'+self.calculate_offset(original_address,address,5)  # jmp [address]
        )   
        # 写入跳转到新内存
        self.pm.write_bytes(original_address,fill_original_code,len(fill_original_code))
        

        # 注入代码，改变坐标==================================================================================
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

        # 注入代码，为了点击主菜单那些===================================================================================
        address += len(assembly_code) +4
        original_address = self.click_menu_address
        original_code = self.pm.read_bytes(original_address,9)
        self.allocate_members.append({
            "name":"click_menu",
            "original_code":original_code,
            "original_address":original_address,
        })

        # 左键点击状态
        self.click_address_1 = self.data_address+68

        GameAssembly_dll_1D7A218 = self.calculate_target_address(original_address+2,original_code[5:9],7)
        # print(GameAssembly_dll_1D7A218)
        # GameAssembly_dll_1D7A218 = self.GameAssembly_dll + 0x1D7A218
        # print(GameAssembly_dll_1D7A218)

        assembly_code=(
            b'\xFF\xD0'+ # call rax
            bytes.fromhex("48 83 F8 01")+ # cmp rax,01
            bytes.fromhex("0F 84 11 00 00 00")+ # je 0x11
            b'\x48\x8B\x05' + self.calculate_offset(address+12,self.click_address_1,7)+ # mov rax,[click_address]
            bytes.fromhex("C7 05")+ self.calculate_offset(address+19,self.click_address_1,10)+bytes.fromhex("00 00 00 00")+ # mov [click_address],00000000
            b'\x48\x8B\x0D' + self.calculate_offset(address+29,GameAssembly_dll_1D7A218,7)+ # mov rcx,[GameAssembly.dll+1B723D0]
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

        # 注入代码，点击ESC===================================================================================
        address += len(assembly_code) +4
        original_address = self.esc_address
        original_code = self.pm.read_bytes(original_address,6)
        self.allocate_members.append({
            "name":"click_esc",
            "original_code":original_code,
            "original_address":original_address,
        })

        # 点击ESC状态
        # self.click_esc_address = self.data_address+84
        # GameAssembly_dll_31649C = self.calculate_target_address(original_address+2,original_code[3:4],2)
        # # print(GameAssembly_dll_31649C)
        # # GameAssembly_dll_31649C = self.GameAssembly_dll + 0x31649C
        # # print(GameAssembly_dll_31649C)

        # assembly_code=(
        #     b'\x83\x3D'+ self.calculate_offset(address,self.click_esc_address,7)+b'\x00'+ # cmp dword ptr [click_esc_address],00
        #     bytes.fromhex("0F 84 11 00 00 00")+ # je 0x11
        #     b'\x8B\x1D'+ self.calculate_offset(address+13,self.click_esc_address,6)+ # mov ebx,[click_esc_address]
        #     b'\x83\xEB\x01'+ # sub ebx,01
        #     b'\x89\x1D'+ self.calculate_offset(address+22,self.click_esc_address,6) + # mov [click_esc_address],ebx
        #     b'\xB0\x01'+ # mov al,01
        #     b'\x84\xC0'+ # test al,al
        #     b'\x0F\x85'+self.calculate_offset(address+32,GameAssembly_dll_31649C,6)+ # jne GameAssembly.dll+301921
        #     b'\x31\xD2' # xor edx,edx
        #     b'\xE9'+ self.calculate_offset(address+40,original_address+6,5) # jmp return
        # )

        # # 写入到新申请的内存
        # self.pm.write_bytes(address,assembly_code,len(assembly_code))

        # fill_original_code = (
        #     b'\xE9'+self.calculate_offset(original_address,address,5)+  # jmp [address]
        #     b'\x90' # nop
        # )
        # # 写入跳转到新内存
        # self.pm.write_bytes(original_address,fill_original_code,len(fill_original_code))
        
        # 注入代码，指定植物id===================================================================
        address += len(assembly_code) +4
        original_address = self.select_plants_address
        self.allocate_members.append({
            "name":"select_plantsid",
            "original_code":self.pm.read_bytes(original_address,6),
            "original_address":original_address,
        })

        # 存储植物id的地址 
        self.plantid_address = self.data_address+90

        assembly_code=(
            b'\x8b\x15' + self.calculate_offset(address,self.plantid_address,6)+ # mov edx,[plantid_address]
            b'\x89\x57\x38' + # mov [rdi+38],edx
            b'\x45\x31\xc0' + # xor r8d,r8d
            b'\xE9' + self.calculate_offset(address+12,original_address+6,5)  # jmp return
        )

        # 写入到新申请的内存
        self.pm.write_bytes(address,assembly_code,len(assembly_code))

        fill_original_code = (
            b'\xE9'+self.calculate_offset(original_address,address,5)+  # jmp [address]
            b'\x90' # nop
        )
        # 写入跳转到新内存
        self.pm.write_bytes(original_address,fill_original_code,len(fill_original_code))

        # 注入代码，指定僵尸id===================================================================
        address += len(assembly_code) +4
        original_address = self.select_zombie_address
        self.allocate_members.append({
            "name":"select_zombieid",
            "original_code":self.pm.read_bytes(original_address,6),
            "original_address":original_address,
        })

        # 存储僵尸id的地址 
        self.zombieid_address = self.data_address+96

        assembly_code=(
            b'\x8b\x15' + self.calculate_offset(address,self.zombieid_address,6)+ # mov edx,[plantid_address]
            b'\x89\x57\x40' + # mov [rdi+38],40
            b'\x45\x31\xc0' + # xor r8d,r8d
            b'\xE9' + self.calculate_offset(address+12,original_address+6,5)  # jmp return
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

    def __exit__(self,exc_type, exc_val, exc_tb):
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
    pvzcheat.inject()
    pvzcheat.load_data()

    with pvzcheat:
        while True:
            a = input("输入：")
            if a == "1":
                for i in range(1,11):
                    pvzcheat.shovel_plants(str(i))
            elif a == "2":
                b = input("输入植物id：")
                for i in range(1,11):
                    pvzcheat.plant_plants(int(b),str(i))
            elif a == "3":
                b = input("输入僵尸id：")
                for i in range(1,11):
                    pvzcheat.plant_zombie(int(b),str(i))
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
                b = input("测试次数：")
                pvzcheat.pressure_test(int(b))
            elif a == "10":
                pvzcheat.put_esc()
            elif a== "11":
                print(pvzcheat.get_sun())
            

    