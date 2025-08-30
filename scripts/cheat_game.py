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
        self.control_base_address = self.UnityPlayer_dll+0x1CAD240
        self.mouse_click_base_address = self.UnityPlayer_dll+0x1CB4CA8
        self.fist_frame_address = self.UnityPlayer_dll+0x80FAA0

        # 判断左键点击
        self.mouse_click_in_address = self.GameAssembly_dll+0x475A1D
        # 判断右键点击
        self.mouse_right_in_address = self.GameAssembly_dll+0x475B40    
        # 点击主菜单类的判断
        self.click_menu_address = self.GameAssembly_dll+0x1592CA8
        # 访问了坐标的代码
        self.get_position_address = self.UnityPlayer_dll+0xA1073E

        # 原程序记录赢的那条路
        self.win_in_address = self.GameAssembly_dll+0x4FF246
        # 倍速设置
        # self.speed_address = self.getPointerAddress([0xB8,0xE8],self.speedx_base_address)
        # 指定放置植物
        self.select_plants_address = self.GameAssembly_dll + 0x469C47
        # 指定放置僵尸
        self.select_zombie_address = self.GameAssembly_dll + 0x4699F1
        # 控件地址
        self.control_value = self.pm.read_longlong(self.control_base_address)

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
        # 存鼠标code
        self.mouse_code_address = None
        # 点击多少次
        self.click_num_address = None

        self.game_map = None
        self.zhi_wu = None
        self.tools = None
        self.cost = None
        self.select_to_board = None

        self.allocate_members = []
        self.data_address = None

    def is_key_down(self,keycode:int):
        active_address = self.control_value+0x14f0
        keycode_address = self.getPointerAddress([0],self.control_value+0x38)
        push_address = self.control_value+0x48
        push_address_2 = self.getPointerAddress([4],self.control_value+0x38)
        self.pm.write_int(active_address,1)
        self.pm.write_int(keycode_address,keycode)
        self.pm.write_int(push_address_2,0)
        self.pm.write_int(push_address,1)
        self.pm.write_int(push_address,2)
        self.pm.write_int(push_address_2,1)
        self.pm.write_int(push_address,1)
        self.pm.write_int(push_address,2)
        

    def mouse_click_test(self,keycode:int):
        m_c = self.getPointerAddress([0x80,0x28],self.mouse_click_base_address)
        print(hex(m_c))
        self.pm.write_int(m_c,keycode)
        # print(hex(rdx))

        

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
                self.game_map[str(index_num)] = [x+left,y+top]
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
            self.zhi_wu[str(index_num)] = [x+left,select_pos["1"][1]+top]
            index_num+=1
        with open("data/tools.json", "r", encoding="utf-8") as file:
            self.tools = json.loads(file.read())
        for key in self.tools:
            self.tools[key] = [self.tools[key][0]+left,self.tools[key][1]+top]
        with open("data/cost.json","r",encoding="utf-8") as file:
            self.cost = json.load(file)
        with open("data/select_to_board.json","r",encoding="utf-8") as file:
            self.select_to_board = json.load(file)
        for key in self.select_to_board:
            self.select_to_board[key] = [self.select_to_board[key][0]+left,self.select_to_board[key][1]+top]


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

    def mouse_left_click(self,delay=0.016):
        self.pm.write_int(self.mouse_code_address,8)
        self.pm.write_int(self.click_num_address,1)
        time.sleep(delay)
    
    def mouse_right_click(self,delay=0.016):
        self.pm.write_int(self.mouse_code_address,16)
        self.pm.write_int(self.click_num_address,1)
        time.sleep(delay)

    def mouse_click(self,x,y,delay = 0.016):
        # self.change_position(x,y)
        # time.sleep(0.01)
        # self.pm.write_int(self.click_address,1)
        # self.pm.write_int(self.click_address_1,1)
        # time.sleep(0.1)
        self.change_position(x,y)
        # time.sleep(0.01)
        self.mouse_left_click(delay)
        


    def click_positoin(self,position:str):
        if position in self.game_map:
            map_x,map_y = self.game_map[position][0],self.game_map[position][1]
            self.mouse_click(map_x,map_y)

    def clear_cache(self):
        self.pm.write_longlong(self.position_address, 0)

    def plant_plants(self,plantid:int,position:str):
        self.pm.write_int(self.plantid_address,plantid)
        # self.change_sun(100000)
        plant_word = "2"
        if position in self.game_map:
            # time.sleep(0.1)
            zhi_wu_x,zhi_wu_y = self.zhi_wu[plant_word][0],self.zhi_wu[plant_word][1]
            self.mouse_click(zhi_wu_x,zhi_wu_y)
            # time.sleep(0.1)
            map_x,map_y = self.game_map[position][0],self.game_map[position][1]

            self.mouse_click(map_x,map_y)
            self.mouse_right_click()
            # time.sleep(0.1)
            # self.pm.write_int(self.right_click_address,1)
            # time.sleep(0.01)
            # self.pm.write_longlong(self.position_address, 0)
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
            # self.pm.write_int(self.right_click_address,1)
            # time.sleep(0.01)
            # self.pm.write_longlong(self.position_address, 0)
            # time.sleep(0.1)
            return True
        else:
            return False


    def shovel_plants(self,position:str):

        chan_x,chan_y = self.tools["shovel"][0],self.tools["shovel"][1]
        # # time.sleep(0.1)
        self.mouse_click(chan_x,chan_y,delay=0.01)
        # time.sleep(0.01)
        # self.is_key_down(49)
        map_x,map_y = self.game_map[position][0],self.game_map[position][1]
        self.mouse_click(map_x,map_y,delay=0.01)
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
            

    def put_esc(self):
        self.is_key_down(27)

    def show_blood(self):
        self.is_key_down(113)
        # self.is_key_down(119)
    
    def save_lineup(self):
        self.mouse_click(self.tools["save_lineup"][0],self.tools["save_lineup"][1])

    def load_lineup(self):
        self.mouse_click(self.tools["load_lineup"][0],self.tools["load_lineup"][1])

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
        self.mouse_click(x,y,delay=0.3)
        time.sleep(0.01)
        self.mouse_click(self.tools["set_zombie"][0],self.tools["set_zombie"][1])
        time.sleep(0.01)
        self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])
        time.sleep(0.01)
        self.mouse_click(x,y,delay=0.3)
        time.sleep(0.01)
        self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])


    def pressure_test(self,n):
        for i in range(n):
            self.mouse_click(self.tools["set_zombie"][0],self.tools["set_zombie"][1])
            self.mouse_click(self.tools["set_zombie"][0],self.tools["set_zombie"][1])
            self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])
            self.mouse_click(self.tools["set_plant"][0],self.tools["set_plant"][1])


    def stuck(self):
        self.is_key_down(27)
        self.is_key_down(27)

    def move_plants(self,start_pos,end_pos):
        if start_pos in self.game_map and end_pos in self.game_map:
            self.mouse_click(self.tools["glove"][0],self.tools["glove"][1])
            x,y = self.game_map[start_pos][0],self.game_map[start_pos][1]
            self.mouse_click(x,y)
            x,y = self.game_map[end_pos][0],self.game_map[end_pos][1]
            self.mouse_click(x,y)
            self.mouse_right_click()
            # self.pm.write_int(self.right_click_address,1)


    def inject(self):
        address = self.allocate_memory(4096, self.GameAssembly_dll)
        free_address = address
        self.data_address = address + 0x800
        print("申请地址：",hex(address))

        # 代码注入，获取赢的那条路========================================================================
        
        # address += len(assembly_code) +4
        original_address = self.win_in_address
        self.allocate_members.append({
            "name":"win_road",
            "original_code":self.pm.read_bytes(original_address,5),
            "original_address":original_address,
            "free_address":free_address
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
        

        '''
        一帧的开头
        '''
        address += len(assembly_code) +4
        original_address = self.fist_frame_address
        original_code = self.pm.read_bytes(original_address,7)
        self.allocate_members.append({
            "name":"select_zombieid",
            "original_code":original_code,
            "original_address":original_address,
        })

        self.click_num_address = self.data_address+102
        self.mouse_code_address = self.data_address+108
        temp_num_address = self.data_address+114
        UnityPlayer_1c13978 = self.calculate_target_address(original_address,original_code[3:7],7)
        # print(UnityPlayer_1c13978)
        # UnityPlayer_1c13978 = self.UnityPlayer_dll+0x1c13978
        # print(UnityPlayer_1c13978)

        assembly_code = (
            b'\x83\x3d' + self.calculate_offset(address,self.click_num_address,7) + b'\x00' + # cmp dword ptr [click_num_address],00
            bytes.fromhex("0F 84 3B 00 00 00") + # je 3B
            b'\x83\x3d' + self.calculate_offset(address+13,temp_num_address,7) + b'\x00' + # cmp dword ptr [temp_num_address],00
            bytes.fromhex("0F 85 2E 00 00 00")+ # jne 2E
            b'\xff\x0d'+ self.calculate_offset(address+26,self.click_num_address,6) + # dec [click_num_address]
            b'\x48\x8b\x15'+self.calculate_offset(address+32,self.mouse_click_base_address,7) + # mov,rdx [UnityPlayer.dll+1cb4ca8]
            bytes.fromhex("48 8B 8A 80 00 00 00") + # mov rcx,[rdx+00000080]
            b'\x48\x8b\x05' + self.calculate_offset(address+46,self.mouse_code_address,7) + # mov rax,[mouse_code_address]
            bytes.fromhex("48 89 41 28") + # mov [rcx+28],rax
            b'\xc7\x05' + self.calculate_offset(address+57,temp_num_address,10)+ bytes.fromhex("01 00 00 00") + # mov [temp_num_address],00000001
            bytes.fromhex("E9 0A 00 00 00") + # jmp 0A
            b'\xc7\x05'+self.calculate_offset(address+72,temp_num_address,10)+ bytes.fromhex("00 00 00 00") + # mov [temp_num_address],0
            b'\x40\x38\x3d'+self.calculate_offset(address+82,UnityPlayer_1c13978,7) + # cmp [UnityPlayer.dll+1C13978],dil
            b'\xe9' + self.calculate_offset(address+89,original_address+7,5) # jmp return
        )

        self.pm.write_bytes(address,assembly_code,len(assembly_code))
        fill_original_code = (
            b'\xE9'+self.calculate_offset(original_address,address,5)+  # jmp [address]
            b'\x66\x90' # nop 2
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
    threading.Thread(target=pvzcheat.freeze_sun,daemon=True).start()
    with pvzcheat:
        while True:
            a = input("输入：")
            if a == "1":
                for i in range(1,51):
                    pvzcheat.shovel_plants(str(i))
            elif a == "2":
                b = input("输入植物id：")
                for i in range(1,51):
                    pvzcheat.plant_plants(int(b),str(i))
            elif a == "3":
                b = input("输入僵尸id：")
                for i in range(1,51):
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
            elif a == "12":
                b = input("输入数字：")
                b = int(b)
                
                pvzcheat.is_key_down(b)
            elif a== "13":
                pvzcheat.stuck()
            elif a == "14":
                b = input("输入数字：")
                b = int(b)
                pvzcheat.mouse_click_test(b)
            elif a == "15":
                pvzcheat.mouse_left_click()


    