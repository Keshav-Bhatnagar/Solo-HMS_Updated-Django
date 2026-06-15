<div align="center">
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/django/django-plain-wordmark.svg" alt="Django Logo" width="100"/>
  <h1>🏫 CampusNest (Solo HMS)</h1>
  <p><strong>Next-Generation Hostel Management & Student Ecosystem</strong></p>
</div>

<p align="center">
  <a href="#-features"><img src="https://img.shields.io/badge/Features-Extensive-blueviolet?style=for-the-badge&logo=rocket" alt="Features"></a>
  <a href="#%EF%B8%8F-technology-stack"><img src="https://img.shields.io/badge/Tech-Django%20%7C%20WebSockets-success?style=for-the-badge&logo=django" alt="Tech Stack"></a>
  <a href="#-installation"><img src="https://img.shields.io/badge/Setup-Easy-orange?style=for-the-badge&logo=gear" alt="Setup"></a>
</p>

---

## 🌟 Overview

**CampusNest** transforms traditional, fragmented hostel administration into a unified, intelligent, and highly aesthetic digital ecosystem. It bridges the gap between administrative oversight and student living, providing real-time interactions, streamlined workflows, and a vibrant community platform.

---

## 🚀 Features

### 🏢 **Administrative Command Center**
*   **Intelligent Dashboard:** Real-time metrics, dynamic charts, and financial overviews.
*   **Smart Room Allocation:** Automated and manual assignment algorithms with visual room tracking.
*   **SLA-Driven Maintenance:** Complaint tracking with automated **Urgency Color-Coding** (🔥 flagged if pending > 48hrs) and integrated photo evidence viewers.
*   **Role-Based Access Control:** Secure, multi-tiered staff and warden privileges.

### 🎓 **Student Portal & Services**
*   **Digital Outpass System:** Request, track, and manage leave permissions seamlessly.
*   **Room Change Requests:** Automated workflows for inter-hostel transfers.
*   **Integrated Payments:** Frictionless fee collection powered by **Stripe API**.

### 🤝 **CampusConnect (The Community Hub)**
*   **Real-Time Discussion Center:** True zero-latency WebSocket chat rooms built with **Django Channels & Daphne** for instant peer-to-peer communication and emergency alerts.
*   **Smart Mess Menu:** Dynamic 6x7 weekly matrices for breakfast, lunch, snacks, dinner, and additional meals.
*   **Digital Marketplace:** Secure peer-to-peer textbook and dorm equipment trading.
*   **Lost & Found:** Visual inventory of lost items to help students recover belongings quickly.
*   **Event & Club Management:** Centralized campus life calendar with poster uploads and club affiliations.

---

## 🛠️ Technology Stack

*   **Backend Framework:** Django 4.2+ (Python)
*   **Asynchronous Server:** Daphne & Django Channels (WebSockets)
*   **Database:** SQLite (Development) / PostgreSQL Ready
*   **Frontend Architecture:** Modern Glassmorphism UI, Custom CSS variables, HTML5/Vanilla JS
*   **Payments:** Stripe Integration

---

## 💻 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/solo-hms.git
   cd solo-hms
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv myenv
   # Windows:
   myenv\Scripts\activate
   # macOS/Linux:
   source myenv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your Stripe keys:
   ```env
   STRIPE_PUBLIC_KEY=pk_test_your_key_here
   STRIPE_SECRET_KEY=sk_test_your_key_here
   ```

5. **Run Migrations & Start the Asynchronous Server:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```
   *(Note: Daphne will automatically intercept `runserver` to serve the ASGI application)*

---

## 🎨 UI Aesthetics
Built heavily relying on modern design principles:
*   **Plus Jakarta Sans** typography
*   **Bento-Grid** dashboard layouts
*   Fluid Micro-animations & Glassmorphism cards

---

<div align="center">
  <i>Developed to redefine institutional living.</i>
</div>
