# 🧬 HelixNode: Edge Native LIMS

**HelixNode** is a proof-of-concept **Laboratory Information Management System (LIMS)** that i run entirely on my **Realme 2 Pro (Android phone)**. It processes raw DNA sequences, computes basic genomic metrics on device and stores everything in a local Postgresql database. The whole system operates at the edge with no cloud providers involved.

dont mind any typo

---

## Purpose

I built this to explore how far consumer mobile hardware can go when used as a server instead of a client. The project shows that an ordinary android device can handle genomic workloads, networking and database operations in a fully self hosted environment.

---

## Architecture Overview

<img width="5006" height="2266" alt="HelixNode" src="https://github.com/user-attachments/assets/d7ec28a0-954d-4b8c-9d55-46cda24a3f2b" />


HelixNode runs as a small full stack inside Termux.

### **Local Communications**
Android aggressively manages local TCP ports, which caused my FastAPI backend to lose its connection to Postgresql. I switched to **Unix Domain Sockets** to bypass TCP entirely, this stabilized local communication and reduced overhead.

### **Remote Access**
The phone sits behind mobile CGNAT, so direct port forwarding was not possible. Ngrok also would not connect on this device because Android’s network stack filters certain outbound tunneling protocols. I switched to Cloudflare’s free quick tunnel instead, which exposes the API over standard HTTPS (Port 443) and works reliably through carrier restrictions.

### **Dependency Optimization**
Some Python libraries required heavy native compilation on ARM64, which caused the phone to overheat. I pinned **pydantic** to v1 and rewrote part of the bioinformatics logic in pure Python to avoid large C or Rust builds and keep the runtime lightweight. asyncpg also stalled during installation because it needed native C builds, so i installed clang, make and binutils to let it compile properly on ARM64.

---

## Tech Stack

- **Hardware:** Realme 2 Pro (Snapdragon 660, 4GB RAM, eMMC 5.1 storage)  
- **OS:** Android 10 (Termux)  
- **Backend:** Python 3.12 (FastAPI + Uvicorn)  
- **Database:** PostgreSQL 17 (Unix socket mode)  
- **Networking:** Cloudflare Zero Trust Tunnel
- **Frontend:** Server rendered HTML/js dashboard  

---
## Screenshots

### 1. Dashboard UI with logs
<img width="711" height="836" alt="image" src="https://github.com/user-attachments/assets/1215e7ec-c45a-455f-83f8-939a060fd89d" />

### 2. Server running on my phone
![WhatsApp Image 2025-11-29 at 23 36 18_56e58cf9](https://github.com/user-attachments/assets/3e2d2e30-6086-4a31-ae1a-c36fe5d304a1)



