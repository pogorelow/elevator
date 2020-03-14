# -*- coding: utf-8 -*-
import random
import math

# параметы модели
# задаем дискретность модели. Модель подразумевает расчет за одни сутки
ticks_in_a_day = 86400 # 86400 = 24 x 60 x 60 >> tick = 1 секунда
# всё время в модели измеряется в часах, части часа -- минуты и секунды
eps = 2 / (ticks_in_a_day / 24) # эпсилон = 2 секунды. 
# Эпсилон необходим, чтобы понимать в условиях действительных переменных, что два события происходят одновременно   

# параметры здания и лифтов
building_floors = 40 # высота здания, число этажей
building_floor_heith = 4 # шаг этажа, метров
building_floor_capacity = 250 # число рабочих мест на каждом этаже
building_canteen_floor = 20 # этаж, где находится столовка

lift_count = 12 # число лифтов
lift_capacity = 12 # емкость кабины (чел)
# показатели времени храним в долях часа. Целый час кратен 1
lift_floor_time = 10 * (24 / ticks_in_a_day) # секунд. Время пассивного (без входа-выхода пассажиров) ожидания лифта на этаже
lift_passenger_time = 1 * (24 / ticks_in_a_day)  # секунда. Время входа-выхода одного пассажира. Суммируется безусловно.
# то есть, если из лифта выходит-входит меньше людей, чем 10, то лифт стоит 10 сек.
# если больше людей входят и выходят -- то считает по секунде на каждого

# TBD -- двухэтажные лифты
# TBD -- лифты по разным уровням (напр. 1-20, 21-40)

# Физика лифта в модели принимается следующая:
# отправляясь с этажа лифт набирает скорость с пост.ускорением А, затем движется со скоростью  пост.V, 
# потом замедляется с пост.ускорением А до полной остановки. Здесь мы НЕ будем считать это каждый раз.
# Мы просто посчитаем время движения до первого (второго, третьего и т.д.) следующего этажа и положим в массив
lift_speed = 6 # макс.скорость лифта м/с
lift_acceleration = 2 # ускорение и замедление лифта м/с2


# параметры рабочего времени и особые моменты
workday = 9 # продолжительность рабочего дня в часах

peek_time_1 = 8
peek_time_1_percentage = 20 # первая волна приходов на работу, доля от общего числа
peek_time_2 = 9
peek_time_2_percentage = 60 # вторая --//--
peek_time_3 = 10
peek_time_3_percentage = 20 # третья --//--
peek_time_variance = 0.25 # СКО для прихода на работу
home_time_variance = 0.5  # СКО для ухода домой

technicians_percentage = 1 # доля круглосуточного персонала 
technicians_time = 1 # каждый перемещается хаотично 1 раз в час
technicians_time_variance = 0.5  # 

visitors_percentage = 1 # доля посетителей 
visitors_time = 1 # каждый приходит в случайное время на 1 час

meetings_per_day_count = 1 # число встреч в день
meetings_duration = 1 # длительность встречи, час
meetings_variation = 0.1 # вариативность начала встречи, час

lunch_time_1 = 12
lunch_time_1_percentage = 20 # первая волна походов на обед, доля от общего числа
lunch_time_2 = 13
lunch_time_2_percentage = 60 # вторая --//--
lunch_time_3 = 14
lunch_time_3_percentage = 20 # третья --//--
lunch_time_variance = 0.33  # СКО для походов на обед
lunch_duration = 0.75  # продолжительность обеда

max_wait_time = 0
up_call = 0

# индикатор состояния пассажира. Соответственно: 0, 1, 2
# passenger_state = ('waiting_for_elevator', 'in_elevator', 'on_the_floor')
# надо понять, нужно ли это вообще

# индикатор типа пассажира. Соответственно: 0, 1, 2
# passenger_type = ('general_worker', 'technician', 'visitor')

#############################################################################################################################
# класс пассажир. У нас полный детерминизм -- каждый уже в начале дня знает, что будет делтаь целый день
class Passenger:
#---------------------------------------------------------------------------------------------------------------    
    def __init__(self, ID): # конструктор
        self.ident = ID # номер для идентификации
        # подбираем тип пассажира
        if random.randint(0, 99) < technicians_percentage: # он -- круглосуточный техперсонал?
            self.type = 'technician'
            self.state = 'on_the_floor'
            # устанавливаем специфичные параметры
            self.current_floor = 0
            self.current_floor = random.randint(1, building_floors)  # первоначально находится на Х этаже
            self.state = 'on_the_floor'
            self.next_floor = random.randint(1, building_floors) # адрес первой поездки
            self.next_ride_time = technicians_time_variance + random.normalvariate(technicians_time, technicians_time_variance) # время первой поездки
            # домой не уходит
            # на обед не ходит
            
        elif random.randint(0, 99) < visitors_percentage: # он -- посетитель?
            self.type = 'visitor'
            self.state = 'on_the_floor'
            # устанавливаем специфичные параметры
            self.current_floor = 0  # первоначально находится на 0 этаже
            self.meeting_floor = random.randint(1, building_floors) # где у него встреча  
            self.state = 'on_the_floor'
            self.next_floor = self.meeting_floor  # адрес первой поездки
            # приходит в любое РАБОЧЕЕ время. Время прихода:
            self.meeting_time = random.randint(peek_time_1, peek_time_1 + workday) + random.normalvariate(1, meetings_variation)
            # домой уходит после meetings_duration. Время ухода:
            self.home_time = random.normalvariate((self.meeting_time + visitors_time), meetings_variation) 
            # на обед не ходит
            # первое известное время -- приход на встречу:
            self.next_ride_time = self.meeting_time 
            
        else:
            self.type = 'general_worker' # он -- обычный работник!
            self.state = 'on_the_floor'
            # устанавливаем специфичные параметры
            self.current_floor = 0  # первоначально находится на 0 этаже
            self.native_floor = random.randint(1, building_floors) # выбираем "родной" этаж  
            self.meeting_floor = random.randint(1, building_floors) # где у него встреча  
            self.state = 'on_the_floor'
            self.next_floor = self.native_floor # адрес первой поездки
            
            # задаем время прихода работника в офис:
            if random.randint(0, 99) < peek_time_1_percentage: # он приходит к 8?
                self.work_start_time = random.normalvariate(peek_time_1, peek_time_variance)
            elif random.randint(0, 99) < peek_time_2_percentage: # он приходит к 9?
                self.work_start_time = random.normalvariate(peek_time_2, peek_time_variance)
            else: # он приходит к 10!
                self.work_start_time = random.normalvariate(peek_time_3, peek_time_variance)
            #end if
            # задаем время ухода домой:
            self.home_time = random.normalvariate((self.work_start_time + workday), home_time_variance) 
            
            # задаем время похода на обед
            if random.randint(0, 99) < lunch_time_1_percentage: # он идет на обед в 12?
                self.lunch_time = random.normalvariate(lunch_time_1, lunch_time_variance)
            elif random.randint(0, 99) < lunch_time_2_percentage: # он идет на обед в 13?
                self.lunch_time = random.normalvariate(lunch_time_2, lunch_time_variance)
            else: # он идет на обед в 14!
                self.lunch_time = random.normalvariate(lunch_time_3, lunch_time_variance)
            #end if
            # задаем время возвращение с обеда
            self.lunch_return_time = random.normalvariate((self.lunch_time + lunch_duration), lunch_time_variance) 

            # задаем время похода на встречу
            if random.randint(0, 99) < 50: # идет на встречу до обеда
                self.meeting_time = random.randint(int(self.work_start_time), int(self.lunch_time))
            else:
                self.meeting_time = random.randint(int(self.lunch_return_time), int(self.home_time) + 1 )
            #end if
            self.meeting_time = self.meeting_time + random.normalvariate(0, meetings_variation) # случайная дробная составляющая
            # задаем время возвращение со встречи
            self.meeting_return_time = random.normalvariate((self.meeting_time + meetings_duration), meetings_variation) 

            self.next_ride_time = self.work_start_time # первое известное время -- приход на работу

        #end if
        #end if
        # устанавливаем общие параметры
        self.call_time = 0 # момент вызова лифта, будет определено дальше
        self.lift_selected = -1 # лифт для поездки будет определен дальше
        self.ride_start = 0  # момент нажатия на кнопку
        self.ride_finish = 0 # момент выхода на нужном этаже
        self.plan_wait_time = 0 # время ожидания на текущую поездку, план
        self.fact_wait_time = 0 # время ожидания на текущую поездку, факт

#---------------------------------------------------------------------------------------------------------------    
    def gen_next_ride(self, now_time):  # для любого пассажира в каждый момент времени должен быть определен следующий его этаж
        
        if self.type == 'general_worker':
            if self.current_floor != self.native_floor: # не на рабочем месте
                self.next_floor = self.native_floor # поедет на свой этаж
                if self.current_floor == self.meeting_floor: # поедет со встечи
                    self.next_ride_time = self.meeting_return_time
                elif self.current_floor == building_canteen_floor: # поедет с обеда
                    self.next_ride_time = self.lunch_return_time
                else: # еще не на работе
                    self.next_ride_time = self.work_start_time #  приход на работу
            
            else: # на рабочем месте
                # может поехать или на встречу, или на обед, или домой
                if self.meeting_time < self.lunch_time: # встреча до обеда
                    if now_time <= self.meeting_time: # пойдет на встречу
                        self.next_floor = self.meeting_floor
                        self.next_ride_time = self.meeting_time
                    elif now_time <= self.lunch_time: # пойдет на обед
                        self.next_floor = building_canteen_floor
                        self.next_ride_time = self.lunch_time
                    else: # пойдет домой
                        self.next_floor = 0
                        self.next_ride_time = self.home_time
                    #end if
                
                else: # встреча после обеда
                    if now_time <= self.lunch_time: # пойдет на обед
                        self.next_floor = building_canteen_floor
                        self.next_ride_time = self.lunch_time
                    elif now_time <= self.meeting_time: # пойдет на встречу
                        self.next_floor = self.meeting_floor
                        self.next_ride_time = self.meeting_time
                    else: # пойдет домой
                        self.next_floor = 0
                        self.next_ride_time = self.home_time
                    #end if
                #end if
            #end if
        
        elif self.type == 'technician':
            self.next_floor = random.randint(1, building_floors)  # случайно выбранный этаж (может быть = текущему этажу)
            self.next_ride_time = now_time + technicians_time_variance + random.normalvariate(technicians_time, technicians_time_variance) 
        
        elif self.type == 'visitor':
            if self.current_floor == 0: # еще не на встрече
                self.next_floor = self.meeting_floor # едет на встречу
                self.next_ride_time = self.meeting_time
            else:
                self.next_floor = 0 # только домой
                self.next_ride_time = self.home_time
            #end if
        else: 
            pass # do nothing
        #end if

#---------------------------------------------------------------------------------------------------------------    
    def vector(self):  # для любого пассажира в каждый момент времени должен быть определен вектор движения
        if self.current_floor < self.next_floor:
            vector = 1 # вектор -- пассажир намерен ехать вверх
        elif self.current_floor > self.next_floor:
            vector = -1 # вектор -- пассажир намерен ехать вниз
        else:
            vector = 0 # вектор -- пассажир никуда не едет
        #end if    
        return vector
    
#---------------------------------------------------------------------------------------------------------------    
    def assign_lift(self, lift): # пассажиру назначен лифт, который отвезен его на нужный этаж
        self.lift_selected = lift.ident
        #
        
#---------------------------------------------------------------------------------------------------------------    
    def enter_lift(self, lift): # пассажир зашел в лифт
        self.state = 'in_elevator'
        #
        
#---------------------------------------------------------------------------------------------------------------    
    def exit_lift(self, now_time): # пассажир вышел из лифта
        self.state = 'on_the_floor'
        self.current_floor = self.next_floor
        self.lift_selected = -1
        self.gen_next_ride(now_time) # куда и когда поедет дальше
        
        # собираем данные дня статистики
        self.ride_finish = now_time # фактическое время завершения поездки
        self.fact_wait_time = self.ride_finish - self.ride_start # время ожидания на текущую поездку, факт
        #

#############################################################################################################################
# класс лифт. полностью содержит информацию о физике лифта и его загрузке, а также маршрут
class Lift:
#---------------------------------------------------------------------------------------------------------------    
    def __init__(self, ID): # конструктор
        self.ident = ID # номер для идентификации
        self.passenger_count = 0 # число пассажиров в кабине
        self.current_floor = random.randint(1, building_floors) # 0 # лифт на нулевом этаже
        self.route = []
        self.route.append(self.current_floor) # маршрут состоит из текущего этажа
        self.current_floor_time = lift_floor_time * 24 / ticks_in_a_day # время до отправления с текущего этажа (до закрытия дверей)
        self.on_the_current_floor = -1 # стоит на текущем этаже
        
#---------------------------------------------------------------------------------------------------------------    
    def add_passenger(self, passenger):
        route_length = len(self.route) # длина маршрута, число остановок
        if route_length != 0: # для маршрута ненулевой длины
            max_floor = max(self.route) # максимальный этаж при ходе вверх
            # max_floor_index = self.route.index(max(self.route)) # номер максимального этажа
            min_floor = min(self.route) # минимальный этаж при ходе вниз
            # min_floor_index = self.route.index(min(self.route)) # номер минимального этажа
            # если исходный или целевой этаж пассажира находится между этажами маршрута, 
            # и при этом совпадает направление движения, мы добавляем в маршрут промежуточную точку.
            # однако, возможны варианты, когда требуемая остановка лежит за точкой поворота маршрута 
            # (то, есть, лифт разворачивается и едет в обратную сторону)
            # в таком случае нужно сдвинуть точку разворота на требуемый этаж.
            next_floor = passenger.next_floor # так быстрее
            current_floor = passenger.current_floor # так быстрее
            passenger.assign_lift(self) # прописали пассажиру номер тек.лифта
            #print('passenger', passenger.ident, current_floor, next_floor, passenger.lift_selected)
            
            # сначала для исходной точки
            new_stop_after = -1
            for floor_counter, floor in enumerate(self.route):
                # при сравнениях помним про ленивый алгоритм:
                if (passenger.vector == 1 and floor < current_floor < self.route[floor + 1]) or \
                   (passenger.vector == -1 and floor > current_floor > self.route[floor + 1]) or \
                   (floor != route_length and floor == max_floor and max_floor < current_floor) or \
                   (floor != route_length and floor == min_floor and min_floor > current_floor):
                    # если исходный этаж пассажира находится между этажами маршрута, и совпадает направление движения, добавляем в маршрут
                    # добавляем точки разворота при необходимости
                    new_stop_after = floor
                elif self.route[self.route.index(floor)] == current_floor: # если лифт и так останавливается
                    pass
                #end if     
            #end for
            if  new_stop_after != -1: # необходима корректировка маршрута        
                self.route = self.route[0:new_stop_after] + [current_floor] + self.route[new_stop_after:] # добавляем остановку
            #end if
            
            # повторяем для точки назначения
            new_stop_after = -1
            for floor_counter, floor in enumerate(self.route):
                if (passenger.vector == 1 and floor < next_floor < self.route[floor + 1]) or \
                   (passenger.vector == -1 and floor > next_floor > self.route[floor + 1]) or \
                   (floor != route_length and floor == max_floor and max_floor < next_floor) or \
                   (floor != route_length and floor == min_floor and min_floor > next_floor): 
                    # если целевой этаж пассажира находится между этажами маршрута, и совпадает направление движения, добавляем в маршрут
                    # добавляем точки разворота при необходимости
                    new_stop_after = floor
                elif floor == next_floor: # если лифт и так останавливается
                    pass
                #end if     
            #end for
            if  new_stop_after != -1: # необходима корректировка маршрута        
                self.route = self.route[0:new_stop_after] + [next_floor] + self.route[new_stop_after:] # добавляем остановку
            #end if
           
            # проверяем, нужно ли добавлять новые остановки в конец маршрута:
            new_stop_after = -1
            for floor_counter, floor in enumerate(self.route):
                if floor == current_floor: # мы добавили эту точку раньше
                    new_stop_after = floor
                #end if
            #end for
            if new_stop_after == -1:
                self.route.append(current_floor) # добавляем исходный этаж
            #end if
            
            new_stop_after = -1
            for floor_counter, floor in enumerate(self.route):
                if floor == next_floor: # мы добавили эту точку раньше
                    new_stop_after = floor
                #end if
            #end for
            if new_stop_after == -1:
                self.route.append(next_floor) # добавляем целевой этаж
            #end if
        
        else:  # для маршрута нулевой длины
            self.route.append(current_floor) # добавляем исходный этаж
            self.route.append(next_floor) # добавляем целевой этаж
        #end if
        # других вариантов нет. корректировка маршрута завершена
        #print('маршрут ', self.route)
        
#---------------------------------------------------------------------------------------------------------------    
    def move(self):
        if self.current_floor == self.route[-1] and self.on_the_current_floor == -1: # если ехать некуда
            self.current_floor_time = lift_floor_time  # стоит
            self.on_the_current_floor = -1 # стоит на текущем этаже
        else:# если есть куда ехать, начинаем или продолжаем поездку
            self.current_floor_time -= 1 / (ticks_in_a_day / 24)  # уменьшаем на одну условную секунду
            if self.current_floor_time < 0 and self.on_the_current_floor == -1: # уезжаем с текушего этажа
                self.on_the_current_floor = 0
                # устанавливаем время до следующего этажа
                self.current_floor_time = lift_floor_timings[abs(self.route[1] - lift.current_floor)] + lift_floor_time
                del self.route[0] # удаляем из маршрута текущий этаж
                self.current_floor = self.route[0] # устанавливаем новый текущий этаж
            elif abs(self.current_floor_time - lift_floor_time) < eps: # приехал на этаж
                self.on_the_current_floor = -1 # стоит на текущем этаже
            else:
                pass # просто продолжаем ехать
            #end if
        #end if

#---------------------------------------------------------------------------------------------------------------    
    def arrive(self, floor):
        pass
        
#############################################################################################################################
# калькулятор (функция), возвращает номер лифта или 0, если не смогла
def calculator(passenger, lift_list):
    # 1. вариант -- этажные цифровые панели
    # Расчет состоит из двух фаз. На первой фазе перебираем все лифты и дополняем их маршруты двумя точками 
    # -- началом и концом поездки конкретного пассажира. Затем считаем сумму времени ожидания всех, кто ждет этот лифт 
    # или едет на нём. Суммы складываем в массив, сортируем по возрастанию.
    # На второй фазе считаем количество свободных мест в каждом из лифтов в соответствющих точках маршрута.
    # Если мест достаточно, сажаем пассажира в лифт с наименьшим суммарным временем, если места нет, сажаем в следующий и т.д.
    wait_time_arr = []
    old_route = []
    #print('----------------------------------------------------------')
    for lift_counter, lift in enumerate(lift_list): # перебираем массив лифтов
#---------------------------------------------------------------------------------------------------------------    
        #print('пассажир: ', passenger.ident, passenger.current_floor, passenger.next_floor)
        #print('лифт: ', lift_counter)
        wait_time = 0
        old_route.append(lift.route) # бэкапим старый маршрут
        lift.add_passenger(passenger) # рассчитываем новый маршрут для текущего пассажира на этом лифте
        new_route = lift.route # получаем новый маршрут
#---------------------------------------------------------------------------------------------------------------    
        # рассчитаем тайминги маршурта выбранного лифта
        route_time = []
        for floor_counter, floor in enumerate(lift.route):            
            # в первом приближении считаем время, начиная с последнего известного этажа
            # потом нужно будет добавить realtime по движению от "текущего" на следующий
            route_time.append(lift_floor_timings[abs(floor - lift.current_floor)] + lift_floor_time)
            # в первом приближении считаем, что лифт стоит на каждом этаже фиксированное время
            # потом нужно будет привязать к числу пассажиров в кабине
        #end for        
#---------------------------------------------------------------------------------------------------------------    
        # теперь рассчитаем время ожидания всех пассажиров
        for pax_counter, pax_enum in enumerate(passenger_list):
            if pax_enum.lift_selected == lift.ident: # 'этот пассажир поедет или уже едет в этом лифте
                # значит, для него будем считать функцию ожидания
                # функция ожидания для конкретного пассажира определяется только маршрутом назначенного ему лифта
                # эта функция для пассажира, который ждёт лифта, равна времени от  момента нажатия кнопки до выхода на этаже
                # для упрощения будем считать, что все лифты в момент нажатия кнопки стоят на этажах
                # конечно же, это не так, и дальше мы переделаем 
                i = 0
                found_current_floor = 0 # индикатор
                for floor_counter, floor in enumerate(new_route): # перебираем все этажи маршрута
                    wait_time = wait_time + route_time[i]
                    i += 1
                    if floor == pax_enum.current_floor:
                        found_current_floor = 1 # нашли этаж, где пассажир сядет
                        # это нужно для того, чтобы не остановить счет, 
                        # если лифт проезжает целевой этаж, но без текущего пассажира
                    #end if
                    if found_current_floor == 1 and floor == pax_enum.next_floor: 
                        break # нашли этаж, где пассажир выйдет, дальше не считаем
                    #end if
                #end for
            #end if    
            # делаем то же самое со следующим пассажиром
        #end for
        wait_time_arr.append(wait_time) # добавляем в массив ожиданий
        
    #end for # расчет функций ожидания завершен
    #print('wait_time_arr', wait_time_arr)
    passenger.lift_selected = -1 # удаляем назначение лифта
    lift_no = wait_time_arr.index(min(wait_time_arr)) # возвращаем номер лифта с минимальным показателем
    lift_list[lift_no].add_passenger(passenger) # сажаем пассажира в выбранный лифт
    passenger.plan_wait_time = min(wait_time_arr) # время ожидания на текущую поездку, план
    for lift_counter, lift in enumerate(lift_list): # перебираем массив лифтов
        if lift_counter != lift_no: # для всех лифтов, кроме выбранного
            lift.route = old_route[lift_counter] # возвращаем старый маршрут
        #end if
    #end for

    # далее нужно посмотреть, будет ли на этом этаже место в лифте для этого пассажира,
    # но пока мы пропускаем этот функционал
    
    #
    # 2. вариант -- этажные кнопки "вверх-вниз", панели приказов в лифте
    # 
    # 3. вариант -- этажные одиночные кнопки, панели приказов в лифте
    #
    #print('lift_no', lift_no)
    return lift_no

#############################################################################################################################
# вывод времени в строку (функция), возвращает текст HH.MM.SS
def fmt_time(now_time):
    string_time = str(int(now_time)) + ':' + str(int(divmod(now_time * 60, 60)[1]))+ ':' + str(int(divmod(now_time * 3660, 60)[1]))
    return string_time
    
#############################################################################################################################
# main
#############################################################################################################################
max_wait_time = 0

# просчитываем физику лифтов
lift_max_speed_time = lift_speed / lift_acceleration # время набора макс.скорости
lift_max_speed_distance = lift_acceleration * lift_max_speed_time * lift_max_speed_time / 2 # дистанция набора макс.скорости
lift_floor_timings = []
# каждое движение между этажами состоит из трех фаз: ускорение-движение-замедление
# так как замедление = ускорению, то можно считать, что движение состоит из двух полу-фаз ускорение-движение
# то есть, чтобы получить времена движения, мы можем взять половину дистанции, а потом удвоить полученное время
for i in range(0, building_floors + 1): # число этажет + 1 (мы же помним, в Питоне верхний индекс недостижим)
    if (i * building_floor_heith / 2) < lift_max_speed_distance: 
        # если лифт не успевает разогнаться до макс.скорости за половину расстояния между этажами
        lift_floor_timing = 2 * math.sqrt(i * building_floor_heith / lift_acceleration) # только ускорение-замедление
    else: # лифт разгоняется и потом движется с постоянной скоростью
        lift_floor_timing = 2 * (lift_max_speed_time + (i * building_floor_heith / 2 - lift_max_speed_distance) / lift_max_speed_time)
        # ускорение-движение-замедление
        # нужно обратить внимание, что при i = 0 (то есть, никуда не едем) время тоже = 0, и его тоже записываем в массив
    #end if
    lift_floor_timings.append(lift_floor_timing * (24 / ticks_in_a_day)) # сохраняем в долях часа
    # здесь времена движения в зависимости от расстояния между этажами (0, 1, 2 и т.д.)
#end for

#---------------------------------------------------------------------------------------------------------------    
# создаем массив пассажиров
    passenger_list = []
passenger_count = building_floors * building_floor_capacity # пассажиров будет столько, сколько влезает в здание
for i in range(1, passenger_count+1):
    # передаем порядковый номер, он запишется в ID
    passenger_list.append(Passenger(ID = i)) # добавляем в список пассажиров
    # в этот момент определяется судьба пассажира на ближайшие сутки (см.конструктор)
    # определяется, куда и когда ему ехать
#end for

#---------------------------------------------------------------------------------------------------------------    
# создаем массив лифтов
lift_list = []
for i in range(0, lift_count): # передаем порядковый номер, он запишется в ID
    lift_list.append(Lift(ID = i)) # добавляем в список лифтов    
#end for

#---------------------------------------------------------------------------------------------------------------    
# запускаем модель на обсчет. Дискретность = 1 секунда. Для удобства часы - целые, части часа -- дроби
for i in range(ticks_in_a_day): 
    now_time = i / (ticks_in_a_day / 24) # текущее время - действительное число, для сравнения с часами
    
    # Секция 1. Пассажиры, ожидающие лифт
    # Каждый пассажир, которому пришло время ехать, подходит на площадку и нажимает кнопку нужного этажа
    # В этот момент запускается обсчет всех маршрутов. Маршрут с минимальным суммарным временем ожидания
    # присваивается пассажиру. Пассажир получает номер лифта и остается ожидать. Маршрут лифта корректируется.
    for ID, passenger in enumerate(passenger_list, 1): 
        # перебираем пассажиров, определяем, кому пришло время нажимать на кнопку
        
        if abs(passenger.next_ride_time - now_time) < eps and \
           passenger.state == 'on_the_floor' and passenger.lift_selected == -1 : # ему пора ехать!
            # передаем требуемый этаж в калькулятор
            lift_number = calculator(passenger, lift_list)
            #print('4', ID, lift_number, passenger.state)
            # это валидно для любого типа лифта. 
            # Для лифта с этажными панелями калькулятор будет считать, что он знает этаж для данного пассажира.
            # Для лифта с кнопками "вверх-вниз" калькулятор будет считать, что нажата соответствующая кнопка.
            # Для лифта с одной кнопкой калькулятор будет считать, что нажата кнопка
            # То есть, нужно варьировать только логику в калькуляторе
            # Далее считаем, что пассажир обязательно поедет на лифте, 
            # то есть, для лифта с панелью приказов в кабине будет нажат соответствующий этаж прямо в кабине.
            # Указанные предположения позволят упростить логику в главной программе и следать её универсальной
            if lift_number != -1: # вызов принят
                # переводим пассажира в новое состояние
                up_call = 1
                passenger.state = 'waiting_for_elevator'
                passenger.lift_selected = lift_number
                passenger.ride_start = now_time  # момент нажатия на кнопку
                print('CALL', fmt_time(now_time), passenger.ident, passenger.current_floor, passenger.next_floor, passenger.lift_selected)                    
            else: 
                pass # ничего не делаем, надеемся что само рассосется на следующем тике    
            #end if
        #end if    
    
    
        
        

    

    #end for -- все кнопки нажали

    #---------------------------------------------------------------------------------------------------------------    
    # Секция 2. Двигаем лифты внутри всё того же отсчета времени
    
    # движение лифта будет описываться двумя параметрами: номером текущего этажа
    # и временем до отправления с этого этажа. То есть, в цикле уменьшаем это время.
    # когда лифт отправляется, текущим этажом становится следующая остановка, 
    # а временем -- время до отправления с неё.
    # такой подход позволит оперировать маршрутом лифта непосредственно.
    lf = []
    for lift_counter, lift in enumerate(lift_list): # перебираем массив лифтов
        lift.move() # двигаем по очереди все лифты
        lf.append(lift.current_floor)
    #end for    
        
#    if up_call == 1: print(lf)
    
    #---------------------------------------------------------------------------------------------------------------    
    # Секция 3. Пассажиры заходят в лифты
    
    for ID, passenger in enumerate(passenger_list, 1):
    # Моментом завершения ожидания считаем момент входа пассажира в лифт. Дальше начинается движение.
    # Время движения учитывается отдельно. 
    # Суммарное время ожидания и поездки может использоваться для оценки точности прогнозирования и тонкой настройки модкли
        if passenger.state == 'waiting_for_elevator':
            for lift_counter, lift in enumerate(lift_list): # перебираем массив лифтов
                if lift.on_the_current_floor == -1 and \
                   passenger.lift_selected == lift.ident and \
                   lift.current_floor == passenger.current_floor: # нужный лифт стоит на текущем этаже
                    lift.passenger_count += 1
                    passenger.enter_lift(lift)
                    print('IN__', fmt_time(now_time), lift.passenger_count, passenger.ident, passenger.current_floor, passenger.next_floor, fmt_time((now_time - passenger.ride_start) * 60))
                    break
                #end if
            #end for
        elif passenger.state == 'in_elevator':
            for lift_counter, lift in enumerate(lift_list): # перебираем массив лифтов
               # if lift.ident == passenger.lift_selected:
               #     print(passenger.ident, passenger.next_floor, lift.ident, lift.current_floor)
                if lift.current_floor == passenger.next_floor and \
                    lift.on_the_current_floor == -1 and passenger.lift_selected == lift.ident: # приехали на нужный этаж
                    lift.passenger_count -= 1
                    passenger.exit_lift(now_time)
                    print('OUT_', fmt_time(now_time), passenger.ident, fmt_time(passenger.plan_wait_time * 60), fmt_time(passenger.fact_wait_time * 60))
                    break
                #end if
            #end for
        #end if
    #end for 
        
#end for  
 





























