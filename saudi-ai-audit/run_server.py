"""
Saudi AI Audit Platform - Simple Server Runner
Windows-compatible server startup
"""

if __name__ == "__main__":
    import uvicorn
    from server import app
    
    print("=" * 60)
    print("SAUDI AI AUDIT PLATFORM - LOCAL SERVER")
    print("=" * 60)
    print("Starting platform...")
    print("")
    print("Platform URL: http://localhost:8000")
    print("Dashboard: http://localhost:8000/dashboard") 
    print("API Docs: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
    except Exception as e:
        print(f"Server error: {e}")
        input("Press Enter to exit...")