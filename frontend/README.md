# Thanjavur Procurement Intelligence

This is a comprehensive dashboard for Thanjavur paddy procurement officers to track live DPC forecasts, storage capacity, risk tiers, and flood exposure.

## Getting Started

To run the full stack (backend API + frontend dashboard) automatically:

1. Open PowerShell or a terminal at the project root (`d:\Projects\crop-procurement-system`).
2. Run the start script:
   ```powershell
   .\run.ps1
   ```
3. This will launch the Python backend in the background and start the Next.js frontend server.

Open [http://localhost:3000](http://localhost:3000) with your browser to view the dashboard! 

**Note on Updates:** If the UI does not immediately reflect the latest changes (such as the new Navigation Bar and Paddy Map Markers), please hard-refresh the page (Ctrl + F5 or Cmd + Shift + R) to ensure Next.js displays the current updated UI and clears any cached hot-reload state.

## Manual Start

If you prefer to start only the frontend:
```bash
cd frontend
npm run dev
```

To learn more about Next.js, take a look at the [Next.js Documentation](https://nextjs.org/docs).
