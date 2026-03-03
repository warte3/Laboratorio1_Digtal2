from machine import Pin, mem32
import time, random

led1=Pin(23,Pin.OUT)
led2=Pin(22,Pin.OUT)
led3=Pin(21,Pin.OUT)  
buz=Pin(19,Pin.OUT)

btn1=Pin(18,Pin.IN,Pin.PULL_DOWN)
btn2=Pin(17,Pin.IN,Pin.PULL_DOWN)
btn3=Pin(16,Pin.IN,Pin.PULL_DOWN)
btn4=Pin(27,Pin.IN,Pin.PULL_DOWN)

btn5=Pin(14,Pin.IN,Pin.PULL_DOWN)
btn6=Pin(5,Pin.IN,Pin.PULL_DOWN)
btn7=Pin(12,Pin.IN,Pin.PULL_DOWN)
btn8=Pin(2,Pin.IN,Pin.PULL_DOWN)   #CAMBIO del pin 15 al pin 2, 15 simpre prendido AAAAAAA    

slcI=Pin(25,Pin.IN,Pin.PULL_DOWN)
slcF=Pin(26,Pin.IN,Pin.PULL_DOWN)

GPIO_OUT_REG= const(0x3FF44004) # cambia el estado de los pines
GPIO_IN_REG=  const(0x3FF4403C) # lee el estado de los pines 

# variables globales 
modo_simon = False
salir_simon=False 
salir_juego = False

def terminar_juego(pin):
  global salir_juego
  time.sleep_ms(20) 
  if (mem32[GPIO_IN_REG] >> 26) & 1:
    salir_juego=True 

slcF.irq(trigger=Pin.IRQ_RISING,handler=terminar_juego)#irq hace que el boton funcione como interupcion,traigger es el que revisa si esta activado, handler llama la funcion de la que quiero ejucutar  

def leer_pin(pin):
    return(mem32[GPIO_IN_REG] >> pin) & 1 #mem32[..]lee el registro del pin,>> pin desplaza os bits a la derecha pin posiciones, & 1 se queda con el bit menos significativo

def rebote(pin,debounce_ms=120):
  if leer_pin(pin)==1:
    time.sleep_ms(debounce_ms)
   
    if leer_pin(pin)==1:
      while leer_pin(pin)==1: # mientras el boton este precionado entrega un 1 cuando lo suelta entrega 0 
        pass
        return True
  return False

def toggle_simon(pin):
  global modo_simon,salir_simon
  time.sleep_ms(20)
  if leer_pin(13):
    while leer_pin(13) :  # espera a que se suelte el boton 
      pass
    time.sleep_ms(200) 
    if not modo_simon: # revisa el estado de la variable 
      modo_simon = True  # cambia el estado de a  variable 0
      simon()   # inicia el juego 
    else:
      salir_simon = True  # sale del simon y vuelve al reflejo solo marcando la bandera  

btn9= Pin(13, Pin.IN, Pin.PULL_DOWN)
btn9.irq(trigger=Pin.IRQ_RISING, handler=toggle_simon) #irq hace que el boton funcione como interupcion,traigger es el que revisa si esta activado, handler llama la funcion de la que quiero ejucutar  


def sleep_interrup(ms): # con esta funcion cada 10ms me verifica si esta la bandera de salir, este sleep se puede interrumpir 
  global salir_simon
  inicio= time.ticks_ms() #  el sleep time.ticks_ms guarda el tiempo exacto y el inicio guarda el tiempo inicial
  while time.ticks_diff(time.ticks_ms(), inicio) < ms:# calcula cuando tiempo hay entre el inicial y el actual , mientras el tiempo sea menor que ms hasta que se vuelva mayor 
        if salir_simon: 
            return
        if leer_pin(13):
          salir_simon = True # Si está presionado, activa la bandera global
          return
        time.sleep_ms(10)

def mostrar_led(led, duracion_ms=500):
    if led == 1:
        mem32[GPIO_OUT_REG] = (1 << 23)
    elif led  == 2:
        mem32[GPIO_OUT_REG] = (1 << 22)
    elif led == 3:
        mem32[GPIO_OUT_REG] = (1 << 21)
    elif led == 4:
        mem32[GPIO_OUT_REG] = (1 << 19)
    sleep_interrup(500)
    mem32[GPIO_OUT_REG] = 0   # apaga todos los pines
    sleep_interrup(300)

def esperar_boton():
  global salir_simon
  while modo_simon and not salir_simon: # revisar si no se oprimio la interrupcion 
    if leer_pin(13):
      salir_simon=True
      return None
    if rebote(18):
        print('boton 1')
        return 1
    elif rebote(17):
        print('boton 2')
        return 2
    elif rebote(16):
        print('boton 3')
        return 3 
    elif rebote (27):
        print('boton 4')
        return 4 
  return None

# Modo Simon Dice
def simon():
  global modo_simon,salir_simon
  salir_simon= False # limpia, asegurando que este en False 
  print("Iniciando Simon Dice")
  sleep_interrup(1000)
  secuencia=[]
  puntos_s=[]
  ronda=0
  
  while modo_simon and not salir_simon:
    ronda+=1
    print('Ronda',ronda )
    nuevo= random.randint(1,4)
    secuencia.append(nuevo)

    for led  in secuencia: # led in secuencia es para que muestre toda la secuencia guardada
      if salir_simon: break  # chequeos para ver si es True y romper el for 
      mostrar_led(led)
    if salir_simon: break # para salir del while 
    sleep_interrup(500)
      
    for led  in secuencia: # esta es para verificar la secuencia que se ingreso 
      if salir_simon: break 
      respuesta= esperar_boton() # espera el boton 
      if respuesta is None :
        break
      if respuesta != led:
        print('Perdiste La ronda:',ronda)
        print('Puntos Totales:', sum(puntos_s))
        time.sleep(0.5)
        mem32[GPIO_OUT_REG]=0
        modo_simon= False 
        return
    else:
        if not salir_simon and modo_simon:
            puntos_s.append(15*ronda) # mientras avanzas en rondas mas dificiles da mas puntos 
            print ('Ronda Superada + ',15 * ronda,'Puntos')
            sleep_interrup(1000)
  
  print('Puntos Totales Simon:', sum(puntos_s)) # cuando sales por interupcion tambien muestre los puntos obtenidos 
  modo_simon= False 
  salir_simon= False # quita la bandera para que cuando vuelva a ingresar no aparezca de una 
  time.sleep_ms(300)
  mem32[GPIO_OUT_REG] = 0 # apaga todos los leds por si son interrumpidos 
  print('Saliendo del Simon Dice')

#-----------------------------------------------------------------------
def juego_refle():
  global salir_juego
  puntos=[]
  puntos2=[]

  #mem32[GPIO_OUT_REG] ^= (1<<23) # invierte el estado del pin correspondiente

  def jugador():
    if rebote(18)==1 and rebote(14)==0:
      return 1
    elif rebote(18)==1 and rebote(14)==1: #######################################
      return 2
    else:
      return 0

  def esperar_pulsador_correcto (objetivo):    
    inicio = time.ticks_ms()
    while True:
      if salir_juego: return #para revisar y salir del juego 
      if objetivo==1 and rebote(18)==1:
        fin = time.ticks_ms()
        if rebote(17)==1 or rebote(16)==1 or rebote(27)==1: #COSA PARA QUE NO HAGA TRAMPA,NO SIRVE POR LA CONECCION DE LOS BOTONES, TOCA CAMBIAR TODOS LOS BOTONES Y PONERLOS A 5V
          print("Trampos -50 puntos")
          puntos.append(-50)
          return
        else:
          print("\n +10 puntos OMG")
          puntos.append(10)
          return time.ticks_diff (fin,inicio)

      elif objetivo==2 and rebote(17)==1:
        fin = time.ticks_ms()
        if rebote(18)==1 or rebote(16)==1 or rebote(27)==1:
          print("Tramposo -50 puntos")
          puntos.append(-50)
          return
        else:
          print("\n +10 puntos OMG")
          puntos.append(10)
          return time.ticks_diff (fin,inicio)
    
      elif objetivo==3 and rebote(16)==1:
        fin = time.ticks_ms()
        if rebote(18)==1 or rebote(17)==1 or rebote(27)==1:
          print("Tramposo -50 puntos")
          puntos.append(-50)
          return
        else:
          print("\n +10 puntos OMG")
          puntos.append(10)
          return time.ticks_diff (fin,inicio)
    
      elif objetivo==4 and rebote(27)==1:
        fin = time.ticks_ms()
        if rebote(18)==1 or rebote(17)==1 or rebote(16)==1:
          print("Tramposo -50 puntos")
          puntos.append(-50)
          return
        else:  
          print("\n +10 puntos OMG")
          puntos.append(10)
          return time.ticks_diff (fin,inicio)
      else:
        puntos.append(-10)
        return print("\n MUY MALO -10 puntos")


  def esperar_pulsador_correcto2 (objetivo):    
    inicio = time.ticks_ms()
    while True:
      if salir_juego: return #para revisar y salir del juego
      if objetivo==1 and (rebote(18)==1 or rebote(14)==1):
        fin = time.ticks_ms()
        if rebote(18)==1:
          print("\n +10 puntos Jugardor 1 OMG \n -5 puntos Jugador 2 MALO")
          puntos.append(10)
          puntos2.append(-5)
          return time.ticks_diff (fin,inicio)
        elif rebote(14)==1:
          print("\n +10 puntos Jugardor 2 OMG \n -5 puntos Jugador 1 MALO")
          puntos2.append(10)
          puntos.append(-5)
          return time.ticks_diff (fin,inicio)

      elif objetivo==2 and (rebote(17)==1 or rebote(5)==1):
        fin = time.ticks_ms()
        if rebote(17)==1:
          print("\n +10 puntos Jugardor 1 OMG \n -5 puntos Jugador 2 MALO")
          puntos.append(10)
          puntos2.append(-5)
          return time.ticks_diff (fin,inicio)
        elif rebote(5)==1:
          print("\n +10 puntos Jugardor 2 OMG \n -5 puntos Jugador 1 MALO")
          puntos2.append(10)
          puntos.append(-5)
          return time.ticks_diff (fin,inicio)
    
      elif objetivo==3 and (rebote(16)==1 or rebote(12)==1):
        fin = time.ticks_ms()
        if rebote(16)==1:
          print("\n +10 puntos Jugardor 1 OMG \n -5 puntos Jugador 2 MALO")
          puntos.append(10)
          puntos2.append(-5)
          return time.ticks_diff (fin,inicio)
        elif rebote(12)==1:
          print("\n +10 puntos Jugardor 2 OMG \n -5 puntos Jugador 1 MALO")
          puntos2.append(10)
          puntos.append(-5)
          return time.ticks_diff (fin,inicio)
    
      elif objetivo==4 and (rebote(27)==1 or rebote(2)==1):
        fin = time.ticks_ms()
        if rebote(27)==1:
          print("\n +10 puntos Jugardor 1 OMG \n -5 puntos Jugador 2 MALO")
          puntos.append(10)
          puntos2.append(-5)
          return time.ticks_diff (fin,inicio)
        elif rebote(2)==1:
          print("\n +10 puntos Jugardor 2 OMG \n -5 puntos Jugador 1 MALO")
          puntos2.append(10)
          puntos.append(-5)
          return time.ticks_diff (fin,inicio)

      else:
        puntos.append(-10)
        puntos2.append(-10)
        return print("\n MUY MALOS LOS DOS -10 puntos")



  mem32[GPIO_OUT_REG] ^= (1<<23)
  mem32[GPIO_OUT_REG] ^= (1<<22)
  mem32[GPIO_OUT_REG] ^= (1<<21)
  print("\n SELECCIONA JUGADOR")
  time.sleep(3)
  cantidad=jugador() #variable que alamacena cuantos jugadores van a jugar 

  if cantidad==1:
    print("\n 1 Jugador")
    for r in range(5):
      if salir_juego: return #para revisar y salir del juego
      mem32[GPIO_OUT_REG]=0  #apaga todo
      print("\n Ronda",r+1)
      estimulo = random.randint(1,4) #leds

      espera = random.randint (1,10) # tiempo  entero
      time.sleep(espera) # cuanto tienpo se demora en encender 
      if salir_juego: return #para revisar y salir del juego

      if estimulo==1:
        mem32[GPIO_OUT_REG] ^= (1<<23)
        time.sleep(0.5)
      
      elif estimulo==2:
        mem32[GPIO_OUT_REG] ^= (1<<22)
        time.sleep(0.5)
      
      elif estimulo==3:
        mem32[GPIO_OUT_REG] ^= (1<<21)
        time.sleep(0.5)
      
      else:
        mem32[GPIO_OUT_REG] ^= (1<<19)
        time.sleep(1)
      a=esperar_pulsador_correcto(estimulo) # almacena del jugador 1 el tiempo de reaccion 
      print (" Tiempo de reaccion :",a,"ms")
      mem32[GPIO_OUT_REG]=0 
    print("\n SE ACABO \n PUNTOS TOTALES:", sum(puntos))

  elif cantidad==2: # juego para dos jugadores
    print("\n 2 Jugadores")
    for r in range(5):
      if salir_juego: return #para revisar y salir del juego
      mem32[GPIO_OUT_REG]=0  #apaga todo
      print("\n Ronda",r+1)
      estimulo = random.randint(1,4) 

      espera = random.randint (1,10) 
      time.sleep(espera)
      if salir_juego: return #para revisar y salir del juego

      if estimulo==1:
        mem32[GPIO_OUT_REG] ^= (1<<23)
        time.sleep(0.5)
      
      elif estimulo==2:
        mem32[GPIO_OUT_REG] ^= (1<<22)
        time.sleep(0.5)
      
      elif estimulo==3:
        mem32[GPIO_OUT_REG] ^= (1<<21)
        time.sleep(0.5)
      
      else:
        mem32[GPIO_OUT_REG] ^= (1<<19)
        time.sleep(1)
      b=esperar_pulsador_correcto2(estimulo)
      print (" Tiempo de reaccion :",b,"ms")
      mem32[GPIO_OUT_REG]=0 
    print("\n SE ACABO \n PUNTOS JUGADOR 1:",sum(puntos),"\n PUNTOS JUGADOR 2:",sum(puntos2))
  else:
    print("\n No se selecciono jugador")
# Juego continuo 
while True: 
  while not rebote(25):
    pass # para que no me genere errores con  el bucle
  print('....Iniciando Juego....') 
  try:
    juego_refle()
    if  salir_juego:
      raise Exception('---Juego Finalizado---') #es para lanzar un error 'artificial 'y que el except genera el break 
  except Exception as e:
    print(e)
    mem32[GPIO_OUT_REG] = 0
    salir_juego= False 
    continue # vuelve al inicio del bucle y espera el boton