# Stellar Trading Bot

A trading bot for the Stellar network with a Streamlit UI.

## Features

- **UI using Streamlit:** Interactive web interface for managing trades.
- **Stellar Key Input:** Securely input your Stellar key via the sidebar.
- **Real-Time Charts:** Display line and candlestick charts for selected crypto pairs.
- **Trading History:** View your account's trading history as a table and overlay it on the charts.

## Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/SanhyewNg/stellar-trading-bot.git
    cd trading-bot
    ```

2. **Create a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure the application:**

    - **Edit `config/config.yaml`:** 

    Update the configuration file with your Stellar API key and other settings like the trading pair, and initial balance. Example:

    ```yaml
    stellar_api_key: "your-stellar-api-key"
    trading_pair: "XLM/USD"
    initial_balance: 1000
    ```

    > **Note:** Ensure that sensitive information like API keys is not committed to version control. You can add `config/config.yaml` to `.gitignore` or use environment variables instead.

5. **Run the Streamlit app:**

    ```bash
    streamlit run app.py
    ```

6. **Access the application:**

    Open your browser and go to `http://localhost:8501/` to access the Streamlit UI.

## Usage

- **Enter Stellar Key:** Input your Stellar key in the sidebar to initialize the trading bot.
- **Select Chart Type:** Choose between a Line Chart or Candlestick Chart to view price data.
- **Select Trading Pair:** Pick a crypto trading pair (e.g., XLM/USD) to display price charts.
- **View Trading History:** Your account's trading history will be displayed as a table and overlaid on the price charts.

## Project Structure

    ```plaintext
    trading-bot/
    ├── app.py               # Main application file
    ├── README.md            # Project documentation
    ├── requirements.txt     # Project dependencies
    ├── .gitignore           # Files to ignore in version control
    ├── config/              # Configuration files
    │   └── config.yaml      # Main configuration file
    ├── engine/              # Core logic and bot engine
    │   ├── __init__.py
    │   ├── trading_bot.py   # Trading bot class
    │   ├── stellar_api.py   # Stellar API interaction functions
    │   ├── strategy/        # Trading strategies
    │   │   ├── __init__.py
    │   │   └── simple_strategy.py  # Basic trading strategy
    │   └── utils.py         # Utility functions
    ├── tests/               # Unit tests
    │   ├── __init__.py
    │   ├── test_trading_bot.py     # Tests for trading bot
    │   ├── test_stellar_api.py     # Tests for Stellar API functions
    │   └── test_simple_strategy.py # Tests for trading strategy
    └── assets/              # Static assets (e.g., logos, images)
        └── logo.png
    ```

## Testing

1. **Run tests with `pytest`:**

    To run the unit tests, use the following command:

    ```bash
    pytest
    ```

    This will automatically discover and run all test files matching the pattern `test_*.py` in the `tests` directory.

2. **Test Coverage:**

   To check test coverage, you can use the `pytest-cov` plugin. First, install it if you haven't already:

   ```bash
   pip install pytest-cov
   ```

   Then, run the tests with coverage reporting:

   ```bash
   pytest --cov=engine --cov=tests
   ```

   This command will generate a coverage report for the `engine` and `tests` directories, showing which parts of your code are covered by tests.

3. **Test Data and Mocking:**

   - Ensure that your tests cover various scenarios including edge cases.
   - Use mocking for external dependencies and API calls to make your tests reliable and fast.
   - For example, if your strategy interacts with the Stellar API, you might mock the API responses to simulate different trading conditions.

4. **Running Specific Tests:**

   You can run a specific test file or even a single test function. For example, to run tests in `test_stellar_api.py`:

   ```bash
   pytest tests/test_stellar_api.py
   ```

   To run a specific test function:

   ```bash
   pytest -k "test_specific_function" tests/test_stellar_api.py
   ```

5. **Continuous Integration:**

   - Consider integrating tests with Continuous Integration (CI) tools like GitHub Actions, Travis CI, or CircleCI.
   - Set up a CI pipeline to run tests automatically on every push or pull request to ensure code quality and functionality.

6. **Test Output:**

   - Review the test output for any failed tests and address them promptly.
   - Use descriptive test cases and assert statements to make debugging easier.

## Security Considerations

- **API Keys:** Handle API keys securely. Avoid hardcoding them in the source code. Use environment variables or encrypted storage.
- **Sensitive Data:** Ensure that any sensitive data is securely stored and not exposed in logs or error messages.
- **Error Handling:** Implement robust error handling to avoid unexpected crashes and ensure graceful degradation of the application.

## Contribution Guidelines

Contributions are welcome! Please follow these guidelines to contribute to the project:

1. **Fork the repository:**

   Click on the "Fork" button at the top right of the repository page.

2. **Create a new branch:**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes:**

   Implement your feature or fix a bug.

4. **Commit your changes:**

   ```bash
   git commit -m "Description of your changes"
   ```

5. **Push to your fork:**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request:**

   Open a Pull Request from your forked repository to the main branch of this repository.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

- **Streamlit:** For providing an excellent framework for building data apps.
- **Stellar SDK:** For enabling easy integration with the Stellar network.


