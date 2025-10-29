from src.api.app import create_app

def main():
    """Entry point for the API server."""
    print('RUNNING SERVER')
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()