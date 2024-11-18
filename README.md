# Automated Code Development Assistant

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Mitigating Common Issues in Automated Code Development](#mitigating-common-issues-in-automated-code-development)
- [Todo List](#todo-list)
- [Contributing](#contributing)
- [License](#license)

## Overview

The **Automated Code Development Assistant** is a Python-based tool designed to streamline and enhance the software development process. By leveraging the power of the Groq API (compatible with OpenAI's GPT models) and ensuring **Aider compatibility**, this script assists developers in tasks such as implementing features, debugging, optimizing code, and generating coding conventions. 

### Goals

1. **Enhance Developer Productivity**: Automate repetitive and time-consuming tasks to allow developers to focus on more critical aspects of software development.
2. **Maintain Code Quality**: Generate and enforce coding standards through automated documentation and code reviews.
3. **Ensure Compatibility and Flexibility**: Support integration with various Language Learning Models (LLMs) and automated coding assistance tools, promoting a versatile development environment.
4. **Mitigate Risks of LLMs Overriding Code Logic**: Address the challenge where LLMs may unintentionally alter or override existing code logic during automated processes, ensuring that critical codebases remain intact and function as intended.
5. **Facilitate Seamless Collaboration**: Provide interactive prompts and documentation that aid in team collaboration and knowledge sharing.

### Aider Compatibility

**Aider** is an advanced AI-driven development tool that enhances coding efficiency and accuracy. This assistant is designed to be **Aider compatible**, meaning it can seamlessly integrate with Aider's ecosystem to provide enhanced functionalities such as intelligent code suggestions, real-time error detection, and automated refactoring. By ensuring compatibility, the Automated Code Development Assistant allows developers to leverage the strengths of both tools, creating a more robust and efficient development workflow.

### Addressing LLMs Overriding Code Logic

While Large Language Models (LLMs) like those provided by OpenAI offer powerful capabilities in automated code generation and assistance, they come with the inherent risk of inadvertently overriding or altering existing code logic. This can lead to unintended behaviors, bugs, or even security vulnerabilities within the software. The Automated Code Development Assistant tackles this issue through:

- **Selective File Processing**: Users can designate sensitive files that should remain untouched, preventing LLMs from making unintended modifications.
- **Interactive Prompts**: By involving the developer in the decision-making process through prompts, the assistant ensures that changes align with the developer's intentions.
- **Contextual Awareness**: Incorporating context from `context.txt` helps the LLM understand the existing codebase better, reducing the likelihood of conflicting changes.
- **Comprehensive Documentation**: Generating detailed documentation like `CONVENTIONS.md` ensures that coding standards are maintained, guiding the LLM to adhere to predefined guidelines.

These measures collectively help maintain the integrity of the codebase while benefiting from the automation and assistance provided by LLMs.

## Features

- **API Key Management**: Ensures secure access by verifying the presence of the `GROQ_API_KEY` environment variable.
- **Interactive File Selection**: Allows users to select specific files for processing and designate sensitive files that should remain unmodified.
- **Action-Focused Prompts**: Guides users to select actions (e.g., Implement, Debug), focus areas (e.g., Login System, API Endpoint), and subjects (e.g., Python, Vue.js) to tailor the assistance provided.
- **Contextual Prompts**: Incorporates contextual information from a `context.txt` file to provide more accurate and relevant assistance.
- **Conventions Documentation**: Automatically generates or updates a `CONVENTIONS.md` file based on user inputs and task descriptions to enforce coding standards.
- **Interactive Assistant Loop**: Engages in a conversational loop with the user, asking clarifying questions and refining outputs until the task is satisfactorily addressed.
- **User-Agent Verification**: Retrieves and displays the current user-agent string for transparency in API interactions.
- **Aider Compatibility**: Seamlessly integrates with Aider, enhancing functionalities such as intelligent code suggestions and real-time error detection.
- **Multi-LLM Support**: Designed to accommodate integration with various LLMs and automated coding assistance tools, providing flexibility and versatility.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/automated-code-dev-assistant.git
   cd automated-code-dev-assistant
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   *If `requirements.txt` is not provided, install the necessary packages manually:*

   ```bash
   pip install requests questionary inquirer httpx
   ```

## Configuration

1. **Set the Groq API Key**

   The script requires a Groq API key to interact with the Groq/OpenAI API. Set the `GROQ_API_KEY` environment variable:

   - **Unix/Linux/macOS**

     ```bash
     export GROQ_API_KEY='your_api_key_here'
     ```

   - **Windows (Command Prompt)**

     ```cmd
     set GROQ_API_KEY=your_api_key_here
     ```

   - **Windows (PowerShell)**

     ```powershell
     $env:GROQ_API_KEY = "your_api_key_here"
     ```

   *Alternatively, you can add this line to your shell profile (e.g., `.bashrc`, `.zshrc`) to set it permanently.*

2. **Prepare Context File**

   Create a `context.txt` file in the script's directory containing any relevant context or background information that the assistant might need to provide more accurate assistance.

   ```bash
   nano context.txt
   ```

   *Add your context information and save the file.*

## Usage

1. **Run the Script**

   ```bash
   python script_name.py
   ```

   *Replace `script_name.py` with the actual name of the Python script.*

2. **Follow the Interactive Prompts**

   - **Select an Action**: Choose from options like Implement, Debug, Optimize, etc.
   - **Select a Focus**: Select the specific area of focus such as Login System, API Endpoint, etc.
   - **Select a Subject**: Choose the programming language or framework involved.
   - **Select Files**: Choose which files in the current directory and subdirectories to include in the process.
   - **Specify Sensitive Files**: Designate files that should not be modified.
   - **Provide Intent**: Describe the intent or goal of the changes you intend to make.

3. **Review Generated Files**

   - **`initial_prompt.md`**: Contains the structured prompt sent to the assistant.
   - **`CONVENTIONS.md`**: Generated or updated coding conventions based on your inputs.
   - **`prompt.txt`**: Stores the assistant's replies for reference.

4. **Interactive Assistant Loop**

   The script engages in a conversational loop with the assistant. If the assistant asks a question, respond accordingly. Type `'exit'` to terminate the session.

5. **Manual Review**

   After execution, manually review the generated files to ensure accuracy and relevance before proceeding with any code changes.

## Mitigating Common Issues in Automated Code Development

Automated code development tools, while powerful, can introduce several challenges. This script incorporates several strategies to mitigate common issues:

1. **API Key Verification**

   - **Issue**: Unauthorized access or accidental exposure of API keys.
   - **Mitigation**: The script checks for the presence of the `GROQ_API_KEY` environment variable before execution, ensuring that the key is set securely and reducing the risk of accidental exposure.

2. **Selective File Processing**

   - **Issue**: Unintended modifications to critical or sensitive files can break the application.
   - **Mitigation**: Users can specify sensitive files that the script should not modify, safeguarding important parts of the codebase.

3. **Contextual Awareness**

   - **Issue**: Lack of context can lead to irrelevant or incorrect suggestions.
   - **Mitigation**: By incorporating a `context.txt` file, the assistant gains a better understanding of the project's specifics, leading to more accurate and relevant assistance.

4. **Interactive Prompts**

   - **Issue**: Automated tools might make incorrect assumptions about developer intentions.
   - **Mitigation**: The script uses interactive prompts to gather precise information about the desired actions, focus areas, and subjects, ensuring that the assistance provided aligns with the developer's actual needs.

5. **Documentation Generation**

   - **Issue**: Inconsistent coding standards can lead to maintenance challenges.
   - **Mitigation**: Automatically generating or updating a `CONVENTIONS.md` file enforces coding standards and best practices, promoting consistency across the codebase.

6. **Error Handling**

   - **Issue**: Unhandled errors can cause the script to fail silently or behave unpredictably.
   - **Mitigation**: The script includes comprehensive error handling, such as checking for the existence of necessary files and handling API response errors gracefully.

7. **User-Agent Transparency**

   - **Issue**: Lack of transparency in API interactions can complicate debugging and security audits.
   - **Mitigation**: The script retrieves and displays the current user-agent string used in API requests, enhancing transparency and aiding in troubleshooting.

8. **Preventing LLMs from Overriding Code Logic**

   - **Issue**: LLMs may unintentionally modify or override existing code logic, leading to bugs or security vulnerabilities.
   - **Mitigation**: Through selective file processing, contextual awareness, and interactive prompts, the script ensures that critical code segments remain untouched unless explicitly intended by the developer.

## Todo List

Enhancing the **Automated Code Development Assistant** is an ongoing process. Below is a list of planned features and improvements:

1. **Enhanced Security Features**
   - Encrypt sensitive configuration files.
   - Implement OAuth2 for secure API authentication.

2. **Support for Multiple APIs**
   - Integrate with other AI models and APIs for broader functionality.

3. **Advanced File Management**
   - Implement version control integration (e.g., Git hooks) to automate certain tasks.
   - Add functionality to exclude directories or file types via configuration.

4. **Improved User Interface**
   - Develop a graphical user interface (GUI) for a more user-friendly experience.
   - Implement command-line arguments for non-interactive usage.

5. **Extended Documentation Generation**
   - Automatically generate additional documentation files such as `README.md`, `CHANGELOG.md`, etc.
   - Support for customizable documentation templates.

6. **Task Automation**
   - Automate repetitive tasks like testing, linting, and deployment based on user inputs.

7. **Logging and Reporting**
   - Implement detailed logging for easier debugging and auditing.
   - Generate reports summarizing the changes and suggestions made by the assistant.

8. **Internationalization**
   - Support multiple languages for broader accessibility.

9. **Plugin Architecture**
   - Allow users to develop and integrate custom plugins to extend functionality.

10. **Performance Optimization**
    - Optimize the script for faster execution and lower resource consumption.

11. **Multi-LLM Support**
    - Extend compatibility to support various LLMs beyond Groq, providing flexibility in choosing preferred AI models.

12. **Aider Integration Enhancements**
    - Deepen integration with Aider to leverage its advanced features fully.

13. **Community Contributions**
    - Encourage and incorporate contributions from the developer community to expand feature sets and improve existing functionalities.

## Contributing

Contributions are welcome! If you have ideas for new features, bug fixes, or improvements, please open an issue or submit a pull request.

1. **Fork the Repository**

2. **Create a New Branch**

   ```bash
   git checkout -b feature/YourFeature
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add your message here"
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/YourFeature
   ```

5. **Open a Pull Request**

*Please ensure that your contributions adhere to the project's coding standards and include relevant tests where applicable.*

## License

This project is licensed under the [MIT License](LICENSE).

---

*Please note: This script is still in development. While it aims to assist with automated code development, it's essential to manually review all generated files and changes to ensure accuracy and adherence to your project's standards. Additionally, integration with other LLMs and automated coding assistance tools is encouraged to enhance the tool's versatility and effectiveness.*
