GPT4MR

- [ ] WICHTIG: Fehler grund zurück an Anwender schicken, damit ChatGPT versteht warum es nicht geklappt hat
- [ ] Falls GPT nicht nur code sondern den gesamten Text schickt, filtere den Python block heraus (siehe regex im Colab)
- [x] Falls ein seq.write() fehlt, manuell im code hinzufügen
- [ ] 'Sequence' object has no attribute 'gradient_waveforms' -> der fehler kommt öfters, vermutlich in plot_kspace, könnte an der pulseq version liegen, kann man vllt abfangen
- [ ] Besseres Logging: gesendete Scripte zwischenspeichern, zusammen mit den log outputs, um sie bei fehlern analysieren zu können
- [ ] Mehr fehlerdetektierung in der Python ausführung! Syntax fehler, erfundene pypulseq funktionen etc sollten alle dem Nutzer gemeldet werden
- [ ] Assets mit ins git, sonst kann azure-sim nicht überall kompiliert werden
- [ ] Reco bild sollte aus schwarz weiß reco und PD bild bestehen (keine phase) sodass GPT im direkten vergleich kontrast und artefakte erkennen kann
- [ ] Im Fehlerfall anderen prompt zurückschicken, der GPT sagt, das etwas nicht stimmte und verbessert werden muss
