import os
import time

def welcome_screen():
    """Displays an ASCII art welcome screen."""
    ascii_art = """
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠖⢋⠡⣀⢂⡐⡀⢆⡐⠄⣂⠐⣀⠂⠌⡉⢓⢦⣀⢀⣠⠴⠚⠩⠑⡠⢁⢂⡐⠄⣂⠐⡨⠙⢦⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠞⠡⢈⠂⡔⠠⢂⠰⠐⠠⠐⢂⠄⠊⠄⡘⠤⢁⠢⢀⡙⢯⡄⠌⢂⠡⣁⠒⢠⠂⡐⢂⠄⢢⠁⡌⠠⠙⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡞⠡⣈⠡⢂⠡⠠⢁⠂⣄⣣⡼⠶⠷⠚⠞⠶⠶⣴⣂⣡⢂⠐⣈⢷⣈⠂⠥⠐⣈⠂⢂⡑⠈⡄⢃⠐⡈⠤⠑⡘⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠟⠠⢡⠐⡰⠠⢁⣶⠞⡛⢉⠄⡰⢁⠂⡑⠨⠄⠃⢄⠂⡉⢛⠲⣦⣘⣇⣌⣠⣥⣤⠾⠴⠶⠷⠶⠶⠧⣴⣤⣡⣐⣸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⢫⠈⡔⠁⠒⣤⠁⠙⢠⠂⡌⢠⠊⠐⡄⠃⡌⢡⡌⠁⠂⠘⠀⠂⢡⠀⡍⢻⡌⠐⢠⠀⢢⠁⡆⢰⠐⢠⠁⡄⠀⡆⠈⠉⠉⠙⢲⣦⡄⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⡏⠃⠤⠑⢨⠐⡠⠌⡁⠆⢂⠡⠊⠄⡡⠐⡐⢄⣢⣤⡭⠴⠷⠷⠾⠶⠷⠦⡭⣽⣧⣆⠉⡄⢂⠰⠀⢆⣡⣢⣥⡵⣤⢧⡼⣤⣵⣠⣠⣙⠦⣄⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢀⣀⡞⢠⢉⢂⠩⠄⣂⠁⠆⠡⡘⠠⠡⠌⡐⣤⡷⠛⢋⣥⡴⠶⢛⣚⣛⣛⣛⠚⠶⠶⣤⣤⣘⣻⣴⠶⢛⣛⣫⣭⡴⠴⠶⠶⠶⠶⠶⠶⢤⣭⣭⣙⡓⠶⣄⠀⠀
⠀⠀⠀⠀⣠⠞⢋⢹⡃⠆⢂⠌⡐⠢⢠⠉⠤⢑⣠⣵⢶⠟⢋⣥⡴⣛⠯⠖⣪⡽⣿⣶⣦⣤⡉⠉⠉⠓⠒⠦⠭⣝⣒⠛⢋⠉⣤⡤⠶⢓⣿⠿⣿⣿⣿⣭⡑⠒⠲⢬⣙⡛⢿⣄⠀
⠀⠀⢀⡾⢁⠢⠐⣾⠠⢉⠰⢈⡐⢡⠂⠌⣴⠧⠴⠶⠖⡚⣫⠕⠋⠁⠀⣾⣿⣷⣾⣿⠛⢿⣿⡄⠀⠀⠀⠀⠀⠀⠙⣮⠴⠋⠁⠀⢠⣿⣿⣶⣿⡟⠙⣿⣷⠀⠀⠀⠈⠉⠓⢾⡃
⠀⣄⡞⡀⠆⡡⢈⠿⢀⠣⢈⠔⠠⢂⠌⡐⠛⠾⠶⠶⣥⡞⠁⠀⠀⠀⠀⣿⣿⣯⣽⣿⣶⣿⣿⡷⠀⠀⠀⠀⠀⠀⢀⠇⠀⠀⠀⠀⢸⣿⣿⣶⣿⣿⣿⣿⣿⠆⠀⠀⠀⠀⠀⢈⡇
⢀⡿⠀⡔⢁⠒⡠⠊⢄⠡⠊⢄⠃⡌⠰⣀⠃⢂⠆⠡⢈⡙⠲⢤⡀⠀⠈⢿⣿⣿⣿⣿⣿⣿⡿⠃⠀⠀⠀⠀⢀⣠⣾⡀⠀⠀⠀⠀⠘⢿⣿⣿⣿⣿⣿⣿⠟⠀⠀⢀⣀⣤⢴⢻⠀
⡞⠠⢁⠒⡈⠤⢁⠜⡀⢊⡁⠆⢌⠠⠡⠄⢊⡐⠌⣁⠂⡛⠶⣤⣉⡙⠳⠤⠭⡿⣿⣿⣯⣭⠤⠤⠤⠶⠒⡋⢍⣰⡞⢉⡉⠛⡒⠲⠲⠤⠭⠿⠿⠻⢛⠚⠛⠩⢉⠩⡼⠖⠋⠀
⢁⠃⠌⠤⠑⡰⢈⡐⠌⠄⠒⡈⢄⠊⢡⠘⢠⠐⠌⡄⢒⠠⣁⠂⠍⡙⠛⠶⠷⠶⠴⠦⠶⠴⠦⠷⠶⠶⡗⠛⡋⢅⡐⢂⡐⠡⠐⠡⣁⠢⠐⡄⠂⠅⠂⡜⢀⢃⣬⠟⠁⠀⠀⠀⠀
⠌⡈⢄⠣⠘⡀⠆⠰⡈⢌⠡⠌⡐⠌⢂⠜⡀⢊⠔⡐⠨⡐⠄⢊⠔⠠⢃⠂⡔⠀⢆⠰⠈⣔⣰⡼⠖⡋⠥⠑⡠⠂⠔⡠⠲⢧⣭⣐⣀⣂⢥⣠⣁⣮⡴⣶⠚⠉⠁⠀⠀⠀⠀⠀⠀
⠆⡁⢆⠈⡁⠸⢀⠇⠰⠆⡈⢰⠈⢰⠁⢆⠸⠀⡆⡈⢁⠰⡈⠆⡈⠆⡁⠎⡀⢱⣆⡾⠿⠉⢁⠰⠰⠈⣀⠱⢀⠉⠆⡰⠁⠆⡀⠉⠿⣏⠉⠉⠁⠆⡰⠈⢹⡆⠀⠀⠀⠀⠀⠀⠀
⠢⢁⠢⢘⠠⠑⡂⠌⣂⠑⠨⠄⢊⠤⠘⡀⠆⡑⢠⠂⡡⠒⢠⠑⡈⠔⡠⠃⡔⡈⠆⠨⠄⡑⠂⡄⢃⠅⢂⠔⠡⡈⠆⢡⠘⠤⠑⡨⠐⢄⡘⠌⢡⠊⠔⡈⠄⡙⢧⡀⠀⠀⠀⠀⠀
⡑⠂⠌⠄⡃⢡⠐⡡⠄⢊⠡⡘⡀⠆⡑⢨⠐⠌⡰⠠⢡⠘⡀⠆⢡⠂⢡⠒⢠⠡⠌⢡⠘⠠⡑⠨⠄⢊⠄⢊⠤⠁⡜⠠⠌⢂⡑⠤⠉⡄⠢⢘⠠⡘⢠⠑⡨⠐⡈⢧⠀⠀⠀⠀⠀
⠄⡉⠌⢂⠡⢂⠡⡐⠌⢂⠡⡐⠤⠑⡈⠔⡈⠒⠠⢁⠂⠤⢁⠌⡠⠘⠠⠘⡀⠒⠨⠐⡨⠁⡔⠡⠘⡠⠊⢄⠢⢑⠠⡁⠎⢠⠐⠂⡅⢂⡑⢂⠡⡐⢁⠢⠑⡐⠨⡘⡇⠀⠀⠀⠀
⢂⠡⢘⠠⢃⢂⠡⡐⠌⢂⠡⡐⢂⡑⠨⠐⢠⢁⣾⢞⡻⣛⠯⣛⢟⡻⢳⠾⠶⣥⣧⣒⣄⡡⢄⠡⡁⠄⡑⢂⠒⡈⠐⠄⢃⠂⠅⢃⠐⢂⠐⡈⢐⠈⡄⢂⡡⣤⣵⠶⢷⣆⠀⠀⠀
⢂⠡⠂⡅⠢⡈⠔⢠⠉⠤⢁⠢⢁⠔⠡⢈⢦⣟⢣⠎⣕⣮⣱⣎⣖⣩⠧⣍⠳⣜⡰⣍⢫⠝⣫⢛⢟⡳⢾⠶⢶⡬⣵⣬⣦⣼⣴⣬⣴⣦⣼⢤⡷⠾⣞⢻⡙⢇⣣⠛⣦⡟⠀⠀⠀
⢂⠡⠒⡈⠤⢁⠊⡄⢊⠄⢃⠰⠁⢌⠂⢌⣿⢫⢬⡙⣜⢢⠳⡜⣬⠫⡝⣭⠻⠶⢷⢮⢮⣽⣴⣫⣜⣸⣅⠫⢖⡱⡒⢦⠱⣒⠦⣓⠲⡜⣢⠝⣰⢫⣔⣣⣙⣮⣴⠟⠉⠀⠀⠀⠀
⢂⠡⢂⠱⡈⠰⢈⡐⠂⡌⠂⡅⢊⠲⡏⠄⡘⠻⢦⠽⡬⢧⠽⡼⢤⢿⣴⣦⣫⡝⣊⠞⡲⢜⡢⢧⡹⠭⡍⣟⢫⢝⡛⣏⢻⣙⢻⣙⠻⡹⣍⠻⣍⠯⡍⢏⡝⢲⣹⠆⠀⠀⠀⠀⠀
⢦⡁⠆⡁⠆⡑⠂⡄⠃⡄⢃⠌⡄⠢⠹⢧⣔⡁⠢⠐⡠⢂⠂⠔⠂⡄⢠⢀⢉⠩⠙⠛⠓⠷⠷⢮⡴⣯⣼⣦⣭⣖⣍⣲⣃⣎⣱⣌⡳⣑⢎⡳⢜⢲⣙⣎⣼⡵⠋⠀⠀⠀⠀⠀⠀
⣈⣷⣤⣁⠒⡈⠡⠐⢡⠐⠌⡰⠠⣁⠒⡠⢉⠙⡋⠰⢁⢂⡉⠄⡃⠌⢄⠢⢈⠆⢡⠊⢌⠰⠐⡠⠐⢠⠀⡄⣀⠢⢈⠡⢉⡉⠍⡉⠩⢉⠩⣩⠿⠋⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣿⣿⣤⣛⠿⣤⣃⡜⡀⡘⠤⢀⢃⠀⠇⡠⠘⡠⢃⠣⠘⣀⠀⠇⡀⠇⡘⡀⠇⡘⣀⠸⠀⡄⢣⢀⠛⡀⠤⢀⠠⠄⡃⠄⢃⠠⢀⠄⣣⣸⠿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣿⣽⣻⢿⣿⣦⣭⣉⡛⠶⠶⢬⣤⣎⣐⡄⢡⠐⡠⢁⠡⣀⠊⠔⡁⢂⠡⠐⢂⠡⠄⠢⢑⠠⠂⡔⢈⡐⠌⢂⠂⢡⠐⣌⣄⣶⠼⠚⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣿⣳⣿⣻⢾⣻⣟⡿⣿⣷⣦⣦⣄⣢⠉⡩⢉⡙⠙⠛⡓⠶⠺⠶⠦⠥⠦⡭⢤⠶⡬⣥⠦⢦⡥⢦⠦⠴⠬⠦⡿⣶⣿⣏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣿⢷⣯⣟⣿⣽⢾⣟⣷⣯⣟⣿⣻⢿⣿⣿⢿⣾⣷⣷⣶⣶⣥⣦⣵⣬⣶⣴⣦⣶⣤⣤⣼⣤⣴⣦⣬⣼⣶⣿⣿⢿⣯⢿⣷⣦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣿⣟⣾⣽⡾⣯⣿⢾⣻⡾⣽⣾⣻⣟⣾⡽⣯⣷⢯⡿⣽⣯⢿⣻⣟⣯⡿⣽⡾⣯⣟⡿⣯⣟⣯⣟⡿⣯⣟⣷⣯⢿⡾⣟⣷⢿⣻⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""

    # ✅ Adds extra space after each character for better terminal rendering
    formatted_art = "\n".join([" ".join(line) for line in ascii_art.split("\n")])

    os.system("cls" if os.name == "nt" else "clear")  # ✅ Clears the terminal
    print(ascii_art)  # ✅ Prints the ASCII art
    print("🚀 Welcome! Initializing...\n")
    time.sleep(2)  # ✅ Pauses for 2 seconds before continuing
