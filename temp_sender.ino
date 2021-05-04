//https://github.com/milesburton/Arduino-Temperature-Control-Library


// Include the libraries we need
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_SleepyDog.h>
#include <SPI.h>
#include <RH_RF69.h>

// pin 3 is SCL, 2 is SDA
#define ONE_WIRE_BUS 3

#define WAIT_FAST_MS 1000
#define WAIT_SLOW_MS 24000

// comment out to turn off LED
#define LED           13

// don't define to skip reading
#define VBATPIN A9

// test mode is more power hungry
bool test_mode = true;
#define TEST_PIN_1 6
#define TEST_PIN_2 10


// Setup a oneWire instance to communicate with any OneWire devices (not just Maxim/Dallas temperature ICs)
OneWire oneWire(ONE_WIRE_BUS);

// Pass our oneWire reference to Dallas Temperature. 
DallasTemperature sensors(&oneWire);

// arrays to hold device address
DeviceAddress insideThermometer;

/*
 * Setup function. Here we do the basics
 */
void setup(void)
{
  // check if we are jumpered together for test mode
  pinMode(TEST_PIN_2, OUTPUT);
  digitalWrite(TEST_PIN_2, LOW); 
  pinMode(TEST_PIN_1, INPUT_PULLUP);
  test_mode = !digitalRead(TEST_PIN_1);
  
  // start serial port
  Serial.begin(9600);
  
  int i = 0;
  while (!Serial && (i < 20))  {
    // wait for serial port to connect. Needed for native USB
    // Or if it goes for 1 sec, assume its never connecting and move on with life
    delay(50); 
    i++;
  }
  Serial.println("Dallas Temperature IC Control Library Demo");

  // locate devices on the bus
  Serial.print("Locating devices...");
  sensors.begin();
  Serial.print("Found ");
  Serial.print(sensors.getDeviceCount(), DEC);
  Serial.println(" devices.");

  // report parasite power requirements
  Serial.print("Parasite power is: "); 
  if (sensors.isParasitePowerMode()) Serial.println("ON");
  else Serial.println("OFF");
  
  // Assign address manually. The addresses below will beed to be changed
  // to valid device addresses on your bus. Device address can be retrieved
  // by using either oneWire.search(deviceAddress) or individually via
  // sensors.getAddress(deviceAddress, index)
  // Note that you will need to use your specific address here
  //insideThermometer = { 0x28, 0x1D, 0x39, 0x31, 0x2, 0x0, 0x0, 0xF0 };

  // Method 1:
  // Search for devices on the bus and assign based on an index. Ideally,
  // you would do this to initially discover addresses on the bus and then 
  // use those addresses and manually assign them (see above) once you know 
  // the devices on your bus (and assuming they don't change).
  if (!sensors.getAddress(insideThermometer, 0)) Serial.println("Unable to find address for Device 0"); 
  
  // method 2: search()
  // search() looks for the next device. Returns 1 if a new address has been
  // returned. A zero might mean that the bus is shorted, there are no devices, 
  // or you have already retrieved all of them. It might be a good idea to 
  // check the CRC to make sure you didn't get garbage. The order is 
  // deterministic. You will always get the same devices in the same order
  //
  // Must be called before search()
  //oneWire.reset_search();
  // assigns the first address found to insideThermometer
  //if (!oneWire.search(insideThermometer)) Serial.println("Unable to find address for insideThermometer");

  // show the addresses we found on the bus
  Serial.print("Device 0 Address: ");
  printAddress(insideThermometer);
  Serial.println();

  // set the resolution
  sensors.setResolution(insideThermometer, 12);
 
  Serial.print("Device 0 Resolution: ");
  Serial.print(sensors.getResolution(insideThermometer), DEC); 
  Serial.println();

  setup_radio();
}

// function to print the temperature for a device
float printTemperature(DeviceAddress deviceAddress)
{
  // method 1 - slower
  //Serial.print("Temp C: ");
  //Serial.print(sensors.getTempC(deviceAddress));
  //Serial.print(" Temp F: ");
  //Serial.print(sensors.getTempF(deviceAddress)); // Makes a second call to getTempC and then converts to Fahrenheit

  // method 2 - faster
  float tempC = sensors.getTempC(deviceAddress);
  if(tempC == DEVICE_DISCONNECTED_C) 
  {
    Serial.println("Error: Could not read temperature data");
    return;
  }
  Serial.print("Temp C: ");
  Serial.print(tempC);
  Serial.print(" Temp F: ");
  Serial.println(DallasTemperature::toFahrenheit(tempC)); // Converts tempC to Fahrenheit

  return tempC;
}



void loop(void)
{ 
  // call sensors.requestTemperatures() to issue a global temperature 
  // request to all devices on the bus
  Serial.print("Requesting temperatures...");
  sensors.requestTemperatures(); // Send the command to get temperatures
  Serial.println("DONE");
  
  // It responds almost immediately. Let's print out the data
  sendTemperature(printTemperature(insideThermometer)); // Use a simple function to print out the data

  if (test_mode) {
    delay(WAIT_FAST_MS);
  } else {
   //requires Adafruit_SleepyDog
   int towait = WAIT_SLOW_MS;
   while (towait > 0) {
       towait -= Watchdog.sleep(towait);
   }
  }
}

// function to print a device address
void printAddress(DeviceAddress deviceAddress)
{
  for (uint8_t i = 0; i < 8; i++)
  {
    if (deviceAddress[i] < 16) Serial.print("0");
    Serial.print(deviceAddress[i], HEX);
  }
}



// RADIO
#if defined (__AVR_ATmega32U4__) // Feather 32u4 w/Radio
  #define RFM69_CS      8
  #define RFM69_INT     7
  #define RFM69_RST     4
#endif

#define RF69_FREQ 433.

// Singleton instance of the radio driver
RH_RF69 rf69(RFM69_CS, RFM69_INT);

void setup_radio(void)
{
    // Serial should have been started already

  
  pinMode(LED, OUTPUT);    
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, LOW);
 
  Serial.println("Feather RFM69 RX Test!");
  Serial.println();
 
  // manual reset
  digitalWrite(RFM69_RST, HIGH);
  delay(10);
  digitalWrite(RFM69_RST, LOW);
  delay(10);

  if (!rf69.init()) {
    Serial.println("RFM69 radio init failed");
    while (1);
  }
  Serial.println("RFM69 radio init OK!");
  
  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM (for low power module)
  // No encryption
  if (!rf69.setFrequency(RF69_FREQ)) {
    Serial.println("setFrequency failed");
  }
 
  // If you are using a high power RF69 eg RFM69HW, you *must* set a Tx power with the
  // ishighpowermodule flag set like this:
  rf69.setTxPower(20, true);  // range from 14-20 for power, 2nd arg must be true for 69HCW
 
  // The encryption key has to be the same as the one in the server
  uint8_t key[] = { 114, 97, 100, 105, 111, 112, 108, 117, 115, 84, 67, 105, 115, 99, 111, 111};
  rf69.setEncryptionKey(key);
}


int nmsg = 0;

void sendTemperature(float tempC) {

 
  char radiopacket[30] = "TempC:###.###";
  //sprintf (radiopacket, "TempC:%g", tempC);
  dtostrf(tempC ,7, 3, radiopacket+6);
  
#ifdef VBATPIN
  char batstr[10] = ",VBat:#.##";
  dtostrf(get_vbat() ,4, 2, batstr+6);
  strcat(radiopacket, batstr);
#endif


  char nmsgstr[10];
  sprintf(nmsgstr , ",n:%i", nmsg);
  strcat(radiopacket, nmsgstr);
  
  Serial.print("Sending:\""); Serial.print(radiopacket); Serial.println("\"");
  
  // Send a message!
  rf69.send((uint8_t *)radiopacket, strlen(radiopacket));
  rf69.waitPacketSent();
  rf69.sleep();
  nmsg++;

  
  if (test_mode || (nmsg < 3)) {
    digitalWrite(LED, HIGH);
    delay(30);
    digitalWrite(LED, LOW);
    delay(30);
    digitalWrite(LED, HIGH);
    delay(30);
    digitalWrite(LED, LOW);    
  }
}


float get_vbat() {  
  float measuredvbat = analogRead(VBATPIN);
  measuredvbat *= 2;    // we divided by 2, so multiply back
  measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage
  return measuredvbat;
}
