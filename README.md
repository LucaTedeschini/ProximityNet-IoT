# ProximityNet-IoT
TODO

# Installare esp32 su arduino
seguire [questa guida](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html)


# ToDo low level
- [ ] Aggiungere il quarto stato nella macchina a stati finiti nella simulazione (comunicazione tra esp e client)
- [ ] Implementare comunicazione tra esp-32 e Client
- [ ] Verificare che i consumi del BT del datasheet siano validi per il BLE
- [ ] Implementare comunicazione esp-32 -> client
    - [ ] Sistema di cache
    - [ ] Sistema di timer (16 o 32 bit)
    - [ ] Client deve convertire i tempi da "relativo" ad assoluto (timestamp - timer esp)
    
# ToDo high level
- [ ] Strutturare tabelle databse QuestDB
- [ ] Creare workflow completo di invio dei dati
- [ ] Creare simulazione con PyGame di un evento di utilizzo
- [ ] App Android

# ToDo Machine learning
- [ ] Pulizia dei dati
- [ ] Analisi dei dati

# ToDo project
- [ ] Iniziare report LaTeX


# acknowledgements
Example code from [NimBLE](https://github.com/h2zero/NimBLE-Arduino/tree/master)
