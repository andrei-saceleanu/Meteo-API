Tema 2 SPRC
Saceleanu Andrei-Iulian, 343C1

In cadrul temei, s-a realizat o configuratie de containere Docker formata
din 3 componente:

1. Server

- accesibil la portul 6000 (de catre host) si 5000(in container network)
- proceseaza request-urile la endpoint-urile necesare
- se valideaza campurile primite(sa fie cele asteptate
    si sa aiba tipurile corecte)
- se verifica constrangerile de integritate in aplicatie
(altfel se primeste eroare de la baza de date si se raporteaza error 500)

2. Baza de date

- PostgreSQL
- default database: tema2_db, password: sprcpass
- volum asociat si script de initializare setat pentru a crea
    cele 3 tabele necesare

3. Utilitar de gestiune

- pgadmin
- accesibil la localhost:5050
- email: sprc_student@domain.com, password: SPRC

* Server + baza de date plasate in network_server
* Utilitar + baza de date plasate in network_manager