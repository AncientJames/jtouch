import rp2
import machine
import time

machine.freq(125_000_000)

device = None

@rp2.asm_pio(set_init=[rp2.PIO.OUT_LOW])
def capsense():
    mov(isr,null)
    
    # set y to the sample period count, by shifting in a 1 and a bunch of 0s
    set(y, 1)
    in_(y, 1)
    in_(null, 20)
    mov(y, isr)
    
    # clear the counter
    mov(x, invert(null))
    
    label('resample')

    # set pin to input...
    set(pindirs, 0)
    
    label('busy')
    # ...and wait for it to pull high
    jmp(pin, 'high')
    jmp(y_dec, 'busy')
    jmp('done')
    
    label('high')
    # set pin to output and pull low
    set(pindirs, 1)
    set(pins, 0)
    
    # while that's going on, count the time spent outside of the busy loop
    jmp(y_dec, 'dec1')
    jmp('done')
    label('dec1')
    jmp(y_dec, 'dec2')
    jmp('done')
    label('dec2')
    jmp(y_dec, 'dec3')
    jmp('done')
    label('dec3')
    jmp(y_dec, 'dec4')
    jmp('done')
    label('dec4')
    jmp(y_dec, 'dec5')
    jmp('done')
    label('dec5')
    
    # count this cycle and repeat
    jmp(x_dec, 'resample')
    
    
    label('done')
    # time's up - push the count
    mov(isr,x)
    push(block)


u32max = const((1<<32)-1)

class Channel:
    def __init__(self, pin, sm):
        self.warmup = 100
        
        self.level = 0
        self.level_lo = u32max
        self.level_hi = 0
        
        machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.state_machine = rp2.StateMachine(sm, capsense, freq=125_000_000, set_base=machine.Pin(pin), jmp_pin=machine.Pin(pin))
        self.state_machine.active(1)
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.active(0)
            
    def active(self, active):
        self.state_machine.active(active)

    @micropython.native
    def update(self):
        if self.state_machine.rx_fifo() > 0:
            for f in range(5):
                level = u32max - self.state_machine.get()
                
                if self.state_machine.rx_fifo() == 0:
                    break
                
            if self.warmup > 0:
                self.warmup -= 1
            else:
                self.level_lo = min(level, self.level_lo)
                self.level_hi = max(level, self.level_hi)
                
            window = self.level_hi - self.level_lo
                
            if window > 64:
                self.level = 1 - ((level - self.level_lo) / window)
       
class Device:
    def __init__(self, pins):
        self.channels = []
        for i in range(len(pins)):
            self.channels.append(Channel(pins[i], i))
            
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        for c in self.channels:
            c.active(0)
            
    def update(self):
        for c in self.channels:
            c.update()
            
    def level(self, channel):
        return self.channels[channel].level
        





# self test
def main():
    bars = ['⠀', '⡀', '⣀', '⣄', '⣤', '⣦', '⣶', '⣷', '⣿']
    
    with (Device((0, 4, 8, 12))) as touch:
        while True:
            touch.update()
            
            print('\r', end='')
            for c in touch.channels:
                print(f'   {bars[min(len(bars)-1, int(c.level * len(bars)))]}', end='')
                
            time.sleep(0.01)

if __name__ == '__main__':
    main()
