import socket
from os import system
import Config
import Utils


class Client(object):

    def __init__(self, board, host=False):
        self.host = host
        self.board = board
        self.health = self.board.ships_value
        self.config = Config.load()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def play(self):
        # Робимо перший крок, якщо хост
        if self.host:
            self.take_turn()

        # Граємо, поки є живі кораблики
        while not gameover:
            self.wait_response()
            if not gameover:
                self.take_turn()

    # Робимо хід
    def take_turn(self):
        #system('cls')
        print("\n" * 100)
        self.board.print(side_by_side=True)
        print()
        print("Стріляй! Вводь, наприклад, '2 7' для вистрілу в x = 2, y = 7")
        x = 0
        y = 0
        valid = False
        while not valid:
            choice = input("> ")
            split_choice = choice.strip().split(" ")
            # Перевіряємо, чи правильно ввелася клітинка
            if len(split_choice) == 2 and split_choice[0].isnumeric() and split_choice[1].isnumeric():
                x = int(split_choice[0])
                y = int(split_choice[1])
                # Перевірка на розмір поля
                if x in range(grid_size) and y in range(grid_size):
                    valid = True

        # Відправляємо інформацію гравцю про вистріл
        message = {'coordinates': {'x': x, 'y': y}}
        print("Стріляю в ({0}, {1})!".format(x, y))
        self.send_data(Utils.jsencode(message))
        # Приймаємо інфомацію про клітинку, куди був зроблений постріл
        response = Utils.jsdecode(self.recv_data(1024))
        if response['response'] == 'HIT':
            print("Ти попав!")
            self.board.boards[1][y][x] = 'H'
        else:
            print("Промах!")
            self.board.boards[1][y][x] = '-'
        try:
            global gameover
            # Якщо ми потрапили в останній кораблик і хп опонента == 0, то gameover
            if response['gameover'] == True:
                print('Вітаю, ти переміг!')
                gameover = True
        except:
            pass

    # Функція відправки даних
    def send_data(self, message):
        if self.host:
            self.connection.send(message)

        else:
            self.sock.send(message)

    # Функція прийняття даних
    def recv_data(self, buffer=1024):
        if self.host:
            return self.connection.recv(buffer)
        else:
            return self.sock.recv(buffer)

    # Функція очікування відповіді від гравців
    def wait_response(self):
        print("Почекай, поки опонент зробить хід!")
        data = self.recv_data(1024)
        response = Utils.jsdecode(data)
        coordinates = response['coordinates']
        x = coordinates['x']
        y = coordinates['y']
        if self.board.take_shot(x, y):
            hit_response = {'response': 'HIT'}
            self.health -= 1
        else:
            hit_response = {'response': 'MISS'}

        # Перевіряємо свої хп, якщо 0, то програємо
        global gameover
        if self.health == 0:
            hit_response['gameover'] = True
            print('На жаль, ти програв! :(')
            gameover = True

        self.send_data(Utils.jsencode(hit_response))

    # Відкриваємо зєднання для сокетів
    def open_connection(self):
        self.sock.bind((self.config['address'], self.config['port']))
        print("Чекаєм на ip: {0} port: {1}".format(self.config['address'], self.config['port']))
        self.sock.listen(5)
        self.connection, self.address = self.sock.accept()
        print("Гравець підключився: {0}".format(self.address))

    # Підключаємося до хосту
    def connect_to_host(self, host, port):
        self.sock.connect((host, port))


class Board(object):
    def __init__(self, size, ships_to_place):
        self.ships_to_place = ships_to_place
        self.size = size
        self.boards = []
        
        # Створюємо поле гравця
        board = []
        for i in range(size):
            row = []
            for j in range(size):
                row.append('0')
            board.append(row)
        self.boards.append(board)

        # Створюємо поле опонента
        oppBoard = []
        for i in range(size):
            row = []
            for j in range(size):
                row.append('0')
            oppBoard.append(row)
        self.boards.append(oppBoard)


    # Змінюємо клітинку при вистрілі
    def take_shot(self,x,y):
        if self.boards[0][y][x] == '1':
            self.boards[0][y][x] = 'H'
            return True
        else:
            self.boards[0][y][x] = '-'
            return False

    # Розставляємо корбалики на початку гри
    def place_ships(self):
        self.ships_value = sum(self.ships_to_place)
        help = """Саме час поставити свої кораблики!
        x, y, тип, вертикально чи горизонтально(V / H відповідно) 
        Наприклад: 4 5 1 V
        Для появи цього повідомлення повторно введи /help
        """
        #system('cls')
        print("\n" * 100)
        print(help)
        while len(self.ships_to_place) > 0:
            print('*'*20)
            print("Твої кораблики: {0}\n".format(','.join([str(x) for x in self.ships_to_place])))
            self.print()
            entry = input('> ')
            entry = entry.strip().split(' ')

            # Перевіряємо дані на коректність
            if entry[0] == '/help' or len(entry) < 4:
                print(help)
            elif len(entry) == 4 and (entry[0].isnumeric()  # X
                                 and entry[1].isnumeric()  # Y
                                 and entry[2].isnumeric()  # Длина
                                 and entry[3].upper() in "VH")\
                                 and int(entry[2]) in self.ships_to_place:   ## V OR H
                entry = (int(entry[0]), int(entry[1]), int(entry[2]), entry[3].upper())
                if self.check_placement(entry):   # Если ничего не мешает поставить корабль.
                    self.place_ship(entry)
                    self.ships_to_place.remove(entry[2])
                else:
                    print("Не можу поставити, бо кінець поля!")
            else:
                if int(entry[2]) not in self.ships_to_place:
                    print("У тебе немає кораблів такого розміру!")
                else:
                    print("Невірний формат!")

    # Функція для прінту полів
    def print(self, side_by_side=False):
        y = 0
        lines = []
        lines.append("   Твоє поле:" + (" "*((grid_size*2)-12)))
        lines.append("   " + " ".join([str(x) for x in range(grid_size)]))
        lines.append(" ")
        for row in self.boards[0]:
            lines.append(str(y) + "  " + " ".join(row))
            y += 1
        y = 0
        if side_by_side:
            opponent = []
            opponent.append("   Поле опонента:" + (" "*((grid_size*2)-16)))
            opponent.append("   " + " ".join([str(x) for x in range(grid_size)]))
            opponent.append(" ")
            for row in self.boards[1]:
                opponent.append(str(y) + "  " + " ".join(row))
                y += 1
            lines = Utils.myJoin(opponent, lines, " "*10)
        print("\n")
        print("\n".join(lines))

    # Ставимо один кораблик на поле
    def place_ship(self, placement):
        x,y,length,direction = placement
        length = int(length)

        if direction == 'V':
            for ship_y in range(y,y+length):
                self.boards[0][ship_y][x] = '1'
        else:
            for ship_x in range(x, x + length):
                self.boards[0][y][ship_x] = '1'

    # Перевіряємр, чи можна поставити корабличик і чи немає колізії
    def check_placement(self, placement):
        x,y,length,direction = placement

        # Перевіряємо, чи коректне місце виставлення кораблика
        counter = 0
        if direction == 'V':
            valid = y + length <= self.size and x < self.size
        else:
            valid = x + length <= self.size and y < self.size

        while valid and counter < length:
            if direction == 'V':
                valid = self.boards[0][y + counter][x] == '0'
            else:
                valid = self.boards[0][y][x + counter] == '0'
            counter += 1
        return valid


# Запускаємо поле
def setup_board():
    board = Board(grid_size, ships_to_place)
    board.place_ships()
    return board


# Запускаємо кліента
def setup_client(board):
    is_host = False
    choice = ""

    while choice is None or choice == "":
        choice = input("Ти хочеш бути сервером? ([y]/n): ")
        if choice is None or choice == "":
            is_host = True
            break

    if choice.lower() == 'y':
        is_host = True
    client = Client(board, is_host)

    # Якщо хост не підключається до хосту
    if not is_host:
        connected = False
        while not connected:
            host_ip = input("Host IP: ")
            host_port = int(input("Port: "))

            try:
                client.connect_to_host(host_ip, host_port)
                connected = True
            except:
                print("Помилка при підключенні!")
    # Якщо хост то чекаємо опонента
    else:
        print("Чекаємо на опонента...")
        client.open_connection()
    return client


if __name__ == '__main__':

    # Параметри
    grid_size = 10
    ships_to_place = [1, 2, 2, 3, 3, 3, 4] # Для швидкої перевірки гри
    # ships_to_place = [1, 1, 2, 3, 4]
    gameover = False

    try:
        board = setup_board()
        client = setup_client(board)
        client.play()
    except:
        print("Дякую за гру!")

