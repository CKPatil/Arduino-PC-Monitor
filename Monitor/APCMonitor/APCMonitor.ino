#include <Adafruit_GFX.h>    // Core graphics library
#include <Adafruit_TFTLCD.h> // Hardware-specific library
#include <MCUFRIEND_kbv.h>


#define LCD_CS A3 // Chip Select goes to Analog 3
#define LCD_CD A2 // Command/Data goes to Analog 2
#define LCD_WR A1 // LCD Write goes to Analog 1
#define LCD_RD A0 // LCD Read goes to Analog 0

#define LCD_RESET A4 // Can alternately just connect to Arduino's reset pin

//   D0 connects to digital pin 8  
//   D1 connects to digital pin 9  
//   D2 connects to digital pin 2
//   D3 connects to digital pin 3
//   D4 connects to digital pin 4
//   D5 connects to digital pin 5
//   D6 connects to digital pin 6
//   D7 connects to digital pin 7


// Assign human-readable names to some common 16-bit color values:
#define BLACK   0x0000
#define BLUE    0x001F
#define RED     0xF800
#define GREEN   0x07E0
#define CYAN    0x07FF
#define MAGENTA 0xF81F
#define YELLOW  0xFFE0
#define WHITE   0xFFFF

MCUFRIEND_kbv tft(A3, A2, A1, A0, A4);

String inputString="";          // String for buffering the message
boolean stringComplete = false; // Indicates if the string is complete
int stringStart;
int stringLimit;
String cpuString = "";          //CPU-Load
String gpu1String = "";         //GPU-Load Temperature Memory-used
String gpu2String = "";         //GPU-fan percent Speed
String gpu3String = "";         //GPU-core clock memory clock
boolean dataIn = false;


void serialEvent() {
    while (Serial.available()>0) {
      //dataIn=true;
      char inChar = (char)Serial.read();
      inputString += inChar;
      delay(5);
      if (inChar == '/') {
        stringComplete = true;
      }
    }
}

void setup(void) {
  Serial.begin(9600);
  Serial.println(F("TFT LCD test"));
  
  tft.reset();

  uint16_t identifier = tft.readID();
  
  tft.begin(identifier);
  Serial.print("TFT size is "); Serial.print(tft.width()); Serial.print("x"); Serial.println(tft.height());
  tft.setRotation(3);
  tft.setTextSize(2);
  tft.setTextColor(WHITE,BLACK);
  
  //Loading screen
  if(Serial.available()==0){
    dataIn = false;  
  }
  else{
    dataIn = true;
  }
  if(!dataIn){
    while(!dataIn){
      tft.setCursor(220, 160);
      tft.fillScreen(BLACK);
      for(int i=0;i<3;i++){
      tft.print(".");  
      delay(1000);
      }
      delay(250);
      tft.fillScreen(BLACK);
      tft.setCursor(220, 160);
      for(int i=0;i<3;i++){
        tft.print(".");  
        delay(1000);
      }
      tft.fillScreen(BLACK);
    }
  }

  tft.setTextSize(2);tft.setTextColor(WHITE,BLACK);
  tft.fillScreen(BLACK);
  tft.setTextSize(2);tft.setTextColor(WHITE,BLACK);
  tft.setCursor(140, 175);
  tft.print("GPU:");
  tft.setCursor(140, 215);
  tft.print("Fan:");
  tft.setCursor(80, 255);
  tft.print("Core|Mem:");
}

void loop(void) {
    serialEvent();
    if (stringComplete==true) {
    
      // CPU
      stringStart=0;
      stringLimit=0;    
      stringStart = inputString.indexOf("C");
      stringLimit = inputString.indexOf("/" ,stringStart);
      cpuString = inputString.substring(stringStart + 1, stringLimit);
      tft.setCursor(50, 50);
      tft.setTextSize(10);
      tft.setTextColor(WHITE,BLACK);
      tft.print(cpuString);
    
      // GPU 1
      stringStart=0;
      stringLimit=0;
      stringStart = inputString.indexOf("G");
      stringLimit = inputString.indexOf("/", stringStart);
      gpu1String = inputString.substring(stringStart + 1 ,stringLimit);
      tft.setCursor(195, 175);
      tft.setTextSize(2);
      tft.print(gpu1String);
        
      // GPU 2
      stringStart=0;
      stringLimit=0;
      stringStart = inputString.indexOf("F");
      stringLimit = inputString.indexOf("/", stringStart);
      gpu2String = inputString.substring(stringStart + 1 ,stringLimit);
      tft.setCursor(195, 215);
      tft.print(gpu2String);
    
      // GPU 3
      stringStart=0;
      stringLimit=0;
      stringStart = inputString.indexOf("A");
      stringLimit = inputString.indexOf("/", stringStart);
      gpu3String = inputString.substring(stringStart + 1 ,stringLimit);
      tft.setCursor(205, 255);
      tft.print(gpu3String);
    
      stringStart=0;
      stringLimit=0;
      stringComplete = false;
      inputString = "";
    }
  delay(5);
}
