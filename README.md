# Car Agency Module for Odoo 16

## Overview

The `car_agency` module is designed to manage car rental services in Odoo 16. It includes functionalities to manage car brands, individual cars, and rental agencies. The module allows for efficient handling of rental agreements, customer interactions, and fleet management.

## Features

- **Car Brands Management**: Define and manage various car brands.
- **Car Management**: Add and maintain individual car records with details such as model, brand, and rental status.
- **Agency Management**: Create and manage rental agencies, including assigning responsible persons and managing associated cars.
- **Rental Agreements**: Create and manage rental contracts with customers.
- **Smart Buttons**: Quick access to related records and actions.
- **State Transitions**: Manage different states of cars and rentals with automated workflows.
- **Wizards**: Facilitate complex operations with user-friendly wizards.

## Models

### `car.brand`
- `name` (Char): The name of the car brand.

### `car.car`
- `name` (Char): The name of the car.
- `brand_id` (Many2one): The brand of the car.
- `license_plate` (Char): The license plate of the car.
- `state` (Selection): The state of the car (e.g., available, rented, maintenance).

### `car.agency`
- `name` (Char): The name of the agency.
- `responsible_id` (Many2one): The responsible person for the agency.
- `cars_ids` (One2many): List of cars managed by the agency.

### `car.rental`
- `customer_id` (Many2one): The customer renting the car.
- `car_id` (Many2one): The car being rented.
- `start_date` (Date): The start date of the rental.
- `end_date` (Date): The end date of the rental.
- `state` (Selection): The state of the rental (e.g., draft, confirmed, done, cancelled).

### `car.rental.wizard`
- Wizard for creating rental records.

## Installation

1. Clone this repository into your Odoo `addons` directory:
   ```bash
   git clone <repository_url> path/to/odoo/addons/car_agency
2. Update the module list:
   ```bash
   ./odoo-bin -u all -d <your_database>
3. Install the car_agency module from the Odoo Apps menu.

## Usage

    Navigate to the Car Agency app from the Odoo dashboard.
    Use the provided menus to manage car brands, individual cars, and rental agencies.
    Create rental agreements from the Car Rentals menu.
   

