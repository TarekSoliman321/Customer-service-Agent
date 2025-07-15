Banking Customer Support AI
Overview
Banking Customer Support AI is an intelligent virtual assistant designed to enhance the customer service experience for bank customers. Built with a focus on security, empathy, and efficiency, this AI agent assists users with common banking inquiries, account details, and card-related issues, all while maintaining strict data privacy protocols through a robust OTP verification system.

The project leverages Google's Gemini 1.5 Flash model, Langchain, and LangGraph to create a conversational AI agent capable of interacting via both text and voice. It integrates with a MySQL database for fetching customer information and uses an SMTP server for sending OTP emails.

Features
Intelligent Conversational Agent: Powered by Google Gemini 1.5 Flash, capable of understanding and responding to various customer queries.

Secure User Verification: Implements a One-Time Password (OTP) system sent via email to verify user identity before accessing sensitive information.

Database Integration: Connects to a MySQL database (Sakila schema used for demonstration) to retrieve customer details, account balances, and transaction history.

Voice Interface: Offers a hands-free experience with speech-to-text and text-to-speech capabilities for natural voice interactions.

Text Interface: Provides a traditional command-line chat interface for text-based interactions.

Error Handling: Robust error handling for database operations, OTP delivery, and speech processing.

Modular Design: Separates concerns into dedicated modules for database interactions, OTP management, and the AI agent logic.
