# Banking Customer Support AI

---

## Overview

Banking Customer Support AI is an intelligent virtual assistant designed to enhance the customer service experience for bank customers. Built with a focus on **security, empathy, and efficiency**, this AI agent helps users with common banking inquiries, account details, and card-related issues. It maintains strict data privacy through a robust **OTP verification system**.

This project uses **Google's Gemini 1.5 Flash model, Langchain, and LangGraph** to create a conversational AI agent that can interact via both **text and voice**. It integrates with a **MySQL database** for fetching customer information and uses an **SMTP server** for sending OTP emails.

---

## Features

* **Intelligent Conversational Agent:** Powered by Google Gemini 1.5 Flash, it understands and responds to various customer queries effectively.

* **Secure User Verification:** Implements a **One-Time Password (OTP) system** sent via email to verify user identity before accessing any sensitive information.

* **Database Integration:** Connects to a **MySQL database** (using the Sakila schema for demonstration) to retrieve customer details, account balances, and transaction history.

* **Voice Interface:** Offers a hands-free experience with **speech-to-text and text-to-speech** capabilities for natural voice interactions.

* **Text Interface:** Provides a traditional command-line chat interface for text-based interactions.

* **Error Handling:** Features robust error handling for database operations, OTP delivery, and speech processing, ensuring a smooth user experience.

* **Modular Design:** Separates concerns into dedicated modules for database interactions, OTP management, and the core AI agent logic, making the system easy to maintain and expand.
