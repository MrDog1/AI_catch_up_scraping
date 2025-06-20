# Test Environment

This directory contains a complete test environment for AI Catch-up Scraping development and debugging.

## Structure

```
test_env/
├── data/           # Test data files
├── debug/          # Debug scripts and analysis
├── scripts/        # Test automation scripts
└── README.md       # This file
```

## Usage

### Setup Test Environment
```bash
python test_env/scripts/setup_test_env.py
```

### Run Error Processing Tests
```bash
python test_env/scripts/test_error_processing.py
```

### System Integration Tests
```bash
python utils/test_all_systems.py
```

## Features

- **Isolated Testing**: Separate from production environment
- **Real Error Data**: Uses actual Error.csv data for testing
- **Mock Credentials**: Test configurations that don't require real API keys
- **Debug Tools**: Individual component testing and analysis
- **Automated Testing**: Scripts for comprehensive system validation

## Test Data

The `data/` directory contains:
- `error_test_data.csv`: Sample error data for testing
- Test configuration files
- Mock credential files

## Debug Scripts

The `debug/` directory contains:
- Component-specific test scripts
- Validation tools
- Performance analysis scripts
- Error reproduction tools

## Notes

- All test files are excluded from git commits
- Test environment uses separate logging
- No real API calls are made during testing
- Safe for development and debugging