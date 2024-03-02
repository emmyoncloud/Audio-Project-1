from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import tkinter as tk
import threading
import pyaudio
import wave
from pydub import AudioSegment 
import pygame.mixer as pym
from mutagen.mp3 import MP3
import time, os
import socket

playlist = []
current_song = 0
current_song_name = ""
playing = False
stopped = True
autoplay = True
id_ = None
muted = False
recording = False

total_time = 0
converted_total_time = 0
def App():
        pym.init()
         
        def transfer():
            # Define the IP address and port on which the server will listen
            HOST = '192.168.0.144' # change this to your WiFi IP address
            PORT = 49152 # change this to any free port number

            # Get the size of the file to be sent
            file_size = os.path.getsize('output1.mp3')

            # Create a socket object
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Bind the socket object to the IP address and port
            s.bind((HOST, PORT))

            # Listen for incoming connections
            s.listen(1)

            # Wait for a client to connect
            conn, addr = s.accept()
            print('Connected by', addr)
            # Open the file to be sent
            with open('output.mp3', 'rb') as f:
                # Send the file in chunks
                sent_bytes = 0
                while True:
                    data = f.read(32768)
                    if not data:
                        break
                    # Send the chunk to the receiver
                    conn.sendall(data)
                    sent_bytes += len(data)
                    progress = (sent_bytes / file_size) * 100
                    # Send the current progress to the receiver
                    conn.sendall(str(progress).encode())
                    print('File has been sent successfully')
            # Close the connection
            conn.close()
            s.close()


        def receive():
            # Define the IP address and port of the server to connect to
            HOST = '192.168.0.144' # change this to the sender's WiFi IP address
            PORT = 49152 # change this to the same port number used by the server

            # Create a socket object
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect to the server
            s.connect((HOST, PORT))
            # Get the path to the downloads directory

            file_dir = os.path.dirname(os.path.abspath(__file__))

            # Open a new file to write the received data to
            with open(os.path.join(file_dir, 'received_file.mp3'), 'wb') as f:
                received_bytes = 0
                while True:
                    data = s.recv(32768)
                    if not data:
                        break
                    # Write the data to file
                    f.write(data)
                    received_bytes += len(data)
                    # Receive the current progress from the sender
                    print(f"file received...")

            # Close the connection
            s.close()

            
        def openfolder(x=None):
            folder_path = str(filedialog.askdirectory(title='Choose Folder'))
            if folder_path=="":
                return
            mp3_files = []
            for i in os.listdir(folder_path):
                if i.endswith('mp3'):
                    mp3_files.append(f'{folder_path}/{i}')
            
            openandplay(mp3_files)

        def openfiles(x=None):
            new_songs = list(filedialog.askopenfilenames(title="Choose Song(s)", filetypes=(("mp3 Files", "*.mp3" ), )))
            openandplay(new_songs)

        def openandplay(new_songs):
            global playlist
            if new_songs==[]:
                pass
            elif playlist==[]:
                playlist += new_songs
                playsong(0)
            else:
                create_new_playlist = messagebox.askyesno('Audio Player', 'Do you want to create a new playlist?\nIf NO, songs will be added to queue.')
                if create_new_playlist==True:
                    playlist.clear()
                    playlist += new_songs
                    lbl_currenttime.after_cancel(id_)
                    playsong(0)
                else:
                    for i in new_songs:
                        if i in playlist:
                            continue
                        else:
                            playlist.append(i)
                    if len(playlist)>1:
                        lbl_upnexttitle['text'] = os.path.basename(playlist[current_song+1])

            print(playlist)
            
        def playsong(n):
            global stopped, playing, total_time, converted_total_time, current_song_name
            current_song_name = playlist[current_song]
            try:
                lbl_upnexttitle['text'] = os.path.basename(playlist[n+1])
            except IndexError:
                lbl_upnexttitle['text'] = os.path.basename(playlist[0])
                
            playing = True
            stopped = False
            btn_playpause['image'] = icon_pause
            lbl_currenttime['text'] = "00:00"
            slider_progress['value'] = 0
            total_time = MP3(current_song_name).info.length
            converted_total_time = time.strftime('%M:%S', time.gmtime(total_time))
            lbl_totaltime['text'] = converted_total_time
            slider_progress['to'] = total_time

            pym.music.load(playlist[n])
            pym.music.play(loops=0)
            play_time()

        def record():
            if btn_record['text'] == 'RECORD':
                audio = pyaudio.PyAudio()
                stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
                global i
                i = 1
                global frames
                frames = []
                global start_time
                start_time = time.time()

                def record_loop():
                    global frames
                    global start_time
                    global i

                    data = stream.read(1024)
                    frames.append(data)

                    passed = time.time() - start_time
                    secs = passed % 60
                    mins = passed // 60
                    hours = mins // 60
                    record_lbl.config(text=f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}")

                    if btn_record['text'] == 'STOP':
                        root.after(1, record_loop)  # Keep recording
                    else:
                        stream.stop_stream()
                        stream.close()
                        audio.terminate()

                        exists = True
                        while exists:
                            if os.path.exists(f"output{i}.wav"):
                                i += 1
                            else:
                                exists = False

                        sound_file = wave.open(f"output{i}.wav", "wb")
                        sound_file.setnchannels(1)
                        sound_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                        sound_file.setframerate(44100)
                        sound_file.writeframes(b"".join(frames))
                        sound_file.close()
                        # Convert WAV to MP3
                        sound = AudioSegment.from_wav(f"output{i}.wav")
                        sound.export(f"output{i}.mp3", format="mp3")

                        # Delete the original WAV file
                        os.remove(f"output{i}.wav")

                btn_record.config(text='STOP')
                record_loop()


            elif btn_record['text'] == 'STOP':
                btn_record.config(text='RECORD')

        def playbtn(x=None):
            global playing
            if playlist==[] and stopped==True:
                pass
            elif playlist!=[] and stopped==True:
                playsong(current_song)
            elif playlist!=[] and stopped==False:
                if playing==False:
                    btn_playpause['image'] = icon_pause
                    playing = True
                    pym.music.unpause()
                else:
                    btn_playpause['image'] = icon_play
                    playing = False
                    pym.music.pause()

        def nextbtn(x=None):
            slider_progress['value'] = slider_progress['value'] + 10
            pym.music.play(loops=0, start=slider_progress.get())


        def prevbtn(x=None):
            slider_progress['value'] = slider_progress['value'] - 10
            pym.music.play(loops=0, start=slider_progress.get())

        def stop(x=None):
            global stopped, playing
            playing = False
            stopped = True
            btn_playpause['image'] = icon_play
            lbl_upnexttitle['text'] = '\n'
            lbl_currenttime['text'] = '00:00'
            lbl_totaltime['text'] = '00:00'
            slider_progress['value'] = 0
            pym.music.stop()

        def toggle_autoplay():
            global autoplay
            if autoplay==False:
                btn_autoplay['text'] = 'Autoplay: ON'
                autoplay = True
            else:
                btn_autoplay['text'] = 'Autoplay: OFF'
                autoplay = False

        def play_time():
            global id_
            converted_current_time = time.strftime('%M:%S', time.gmtime(int(slider_progress.get())))

            if stopped:
                return
            
            if int(slider_progress.get())==int(total_time):
                if autoplay==True:
                    nextbtn()
                    return
                else:
                    stop()
            elif playing==True:
                next_time = int(slider_progress.get()) + 1
                slider_progress['value'] = next_time
                lbl_currenttime['text'] = converted_current_time
            else:
                pass

            id_ = lbl_currenttime.after(1000, play_time)
            
        def slider(x):
            if not stopped:
                pym.music.play(loops=0, start=slider_progress.get())

        def toggle_mute(x=None):
            global muted
            if muted==False:
                btn_volume['image'] = icon_mute
                pym.music.set_volume(0.0)
                muted = True
            else:
                btn_volume['image'] = icon_unmute
                pym.music.set_volume(slider_volume.get()/100)
                muted = False

        def set_volume(x=0):
            if muted==True:
                return
            pym.music.set_volume(slider_volume.get()/100)

        def pl_play_song():
            global current_song, current_song_name
            s = lst_playlist.curselection()[0]
            if s==current_song:
                messagebox.showinfo("Audio Player", "This song is already playing.")
            else:
                current_song = s 
                current_song_name = playlist[current_song]   
                lbl_currenttime.after_cancel(id_)
                playsong(s)

        def update_playlistbox():
            lst_playlist.delete(0, END)
            for i in playlist:
                lst_playlist.insert(END, os.path.basename(i))

        def pl_shift_up():
            global playlist
            s = lst_playlist.curselection()[0]
            if playlist[s]==current_song_name:
                messagebox.showerror("Audio Player", "This Song is currently playing.\nThis cannot be shifted.")
            else:
                playlist[s], playlist[s-1] = playlist[s-1], playlist[s]
                update_playlistbox()
                if s==0:
                    lst_playlist.selection_set(len(playlist)-1) 
                else:
                    lst_playlist.selection_set(s-1) 

        def pl_shift_down():
            global playlist
            s = lst_playlist.curselection()[0]
            if playlist[s]==current_song_name:
                messagebox.showerror("Audio Player", "This Song is currently playing.\nThis cannot be shifted.")
            else:
                try:
                    playlist[s], playlist[s+1] = playlist[s+1], playlist[s]
                    update_playlistbox()
                    lst_playlist.selection_set(s+1)  
                except IndexError:
                    sd = playlist.pop()
                    playlist = [sd]+playlist
                    update_playlistbox()
                    lst_playlist.selection_set(0)

        def pl_delete_song():
            global playlist
            s = lst_playlist.curselection()[0]
            if playlist[s]==current_song_name:
                messagebox.showerror("Audio Player", "This Song is currently playing.\nThis cannot be deleted.")
            else:
                playlist.pop(s)
                update_playlistbox()
                lst_playlist.selection_set(s)

        def show_playlist():
            global lst_playlist
            if playlist==[]:
                messagebox.showerror("Audio Player", "Playlist is empty. Add some songs first")
            else:
                playlist_window = Toplevel()
                playlist_window.title("Audio Player - Playlist")
                playlist_window.resizable(0,0)

                lst_playlist = Listbox(playlist_window,activestyle="underline", background="black", fg='pink', selectmode=SINGLE, width=80, selectbackground='pink', selectforeground='black')
                lst_playlist.grid(column=0, padx=10, pady=10, row=0)

                frm_buttons = Frame(playlist_window, height=200, width=200)
                frm_buttons.grid(column=1, row=0)
                btn_shiftup = Button(frm_buttons, text='Shift Up', width=8, command=pl_shift_up)
                btn_shiftup.grid(column=0, padx=5, pady=5, row=0)
                btn_shiftdown = Button(frm_buttons, text='Shift Down', width=8, command=pl_shift_down)
                btn_shiftdown.grid(column=0, padx=5, pady=5, row=1)
                btn_play = Button(frm_buttons,text='Play Song', width=8, command=pl_play_song)
                btn_play.grid(column=0, padx=5, pady=5, row=2)
                btn_remove = Button(frm_buttons, text='Remove ', width=8, command=pl_delete_song)
                btn_remove.grid(column=0, padx=5, pady=5, row=3)

                update_playlistbox()
                lst_playlist.selection_set(current_song)   

                playlist_window.mainloop()

        def close():
            pym.music.stop()
            root.destroy()

        root = Tk()
        root.title("Group")
        root.geometry('500x390')
        root.resizable(0, 0)


        icon_play = PhotoImage(file='icons/play.png')
        icon_pause = PhotoImage(file='icons/pause.png')
        icon_open = PhotoImage(file='icons/open.png')
        icon_next = PhotoImage(file='icons/next.png')
        icon_previous = PhotoImage(file='icons/previous.png')
        icon_stop = PhotoImage(file='icons/stop.png')
        icon_mute = PhotoImage(file='icons/mute.png')
        icon_unmute = PhotoImage(file='icons/unmute.png')

        menubar = Menu(root)
        root.config(menu=menubar)

        menu_file = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=menu_file)
        menu_file.add_command(label="Open File(s)           Ctrl+O", command=openfiles)
        menu_file.add_command(label="Open Folder            Ctrl+F", command=openfolder)



        frm_controls = Frame(root)
        frm_controls.grid(row=1, column=0, pady=10)
        btn_previous = Button(frm_controls, image=icon_previous, borderwidth=0, command=prevbtn)
        btn_previous.grid(row=1, column=1, padx=2, pady=2)
        btn_playpause = Button(frm_controls, image=icon_play, borderwidth=0, command=playbtn)
        btn_playpause.grid(row=1, column=2, padx=10, pady=2)
        btn_next = Button(frm_controls, image=icon_next, borderwidth=0, command=nextbtn)
        btn_next.grid(row=1, column=3, padx=10, pady=2)
        btn_stop = Button(frm_controls, image=icon_stop, borderwidth=0, command=stop)
        btn_stop.grid(row=1, column=0, padx=10, pady=2)
        btn_open = Button(frm_controls, image=icon_open, borderwidth=0, command=openfiles)
        btn_open.grid(row=1, column=5, padx=10, pady=2)
        
        frm_adcontrols = Frame(root)
        frm_adcontrols.grid(row=2, column=0)
        btn_autoplay = Button(frm_adcontrols, text="Autoplay: ON", command=toggle_autoplay)
        btn_autoplay.grid(row=0, column=0, pady=10, padx=5)
        btn_playlist = Button(frm_adcontrols, text='Show Playlist', command=show_playlist)
        btn_playlist.grid(row=0, column=1, pady=10, padx=5)

        lbl_volume = LabelFrame(frm_adcontrols, text='VOLUME', font=('consolas', 11, 'bold'), relief=RIDGE)
        lbl_volume.grid(row=0, column=2, pady=10)
        btn_volume = Button(lbl_volume, text='Volume', image=icon_unmute, borderwidth=0, command=toggle_mute)
        btn_volume.grid(row=0, column=0, padx=5, pady=3)
        slider_volume = ttk.Scale(lbl_volume, from_=0, to=100, orient=HORIZONTAL, length=150, value=100, command=set_volume)
        slider_volume.grid(row=0, column=1, padx=5, pady=3)

        frm_progress = LabelFrame(root)
        frm_progress.grid(row=3, column=0)
        lbl_currenttime = Label(frm_progress, text="00:00")
        lbl_currenttime.grid(row=0, column=0, padx=10)
        slider_progress = ttk.Scale(frm_progress, from_=0, to=100, orient=HORIZONTAL, length=365, value=0, command=slider)
        slider_progress.grid(row=0, column=1, pady=20)
        lbl_totaltime = Label(frm_progress, text="00:00")
        lbl_totaltime.grid(row=0, column=2, padx=10)

        btn_record = tk.Button(frm_controls, text="RECORD", font=("Arial", 13, "bold" ), command=record)
        btn_record.grid(row=0, column=0, padx=3, pady=1)
        btn_transfer = tk.Button(frm_controls, text="TRANSFER", font=("Arial", 13, "bold" ), command=transfer)
        btn_transfer.grid(row=0, column=2, padx=3, pady=1)
        btn_receive = tk.Button(frm_controls, text="RECEIVE", font=("Arial", 13, "bold" ), command=receive)
        btn_receive.grid(row=0, column=3, padx=3, pady=0)
        record_lbl = tk.Label(frm_controls, text="00:00:00")
        record_lbl.grid(row=0, column=1, padx=3, pady=10)
        lbl_upnext = LabelFrame(root, text="CURRENTLY PLAYING", font=('consolas', 11, 'bold'), relief=RIDGE)
        lbl_upnext.grid(row=4, column=0, padx=3, pady=10)
        lbl_upnexttitle = Label(lbl_upnext, text='\n', font=('consolas', 10), width=60, wraplength=480)
        lbl_upnexttitle.grid(row=0, column=0)

        root.bind('<space>', playbtn)
        root.bind('m', toggle_mute)
        root.bind('n', nextbtn)
        root.bind('p', prevbtn)
        root.bind('<Control-o>', openfiles)
        root.bind('<Control-f>', openfolder)
        root.bind('x', stop)


        root.protocol("WM_DELETE_WINDOW", close)
        root.mainloop()

App()