# Cloud Cost AI - Frontend

Modern React dashboard for AWS cost monitoring, anomaly detection, and budget management with real-time alerts.

## Overview

The frontend is a **Vite-powered React application** that provides a comprehensive FinOps dashboard with the following features:

- 📊 **Spend Overview** - Visualize AWS costs over time with interactive charts
- 🔍 **Anomaly Detection** - AI-powered detection of unusual spending patterns
- 📈 **Resource-Level Costs** - Deep dive into individual resource costs
- 💰 **Budget Management** - Set and monitor per-service budgets with alerts
- ⚠️ **Burn Rate Analysis** - Track projected spending vs budgets

## Tech Stack

- **Framework**: React 19
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 4.1.17
- **HTTP Client**: Axios
- **Charts**: Recharts 3.3.0
- **Date Handling**: date-fns

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   ├── costService.js          # AWS cost API calls
│   │   └── resourceService.js      # Resource-level cost queries
│   ├── components/
│   │   ├── CostChart.jsx           # Cost trend visualization
│   │   ├── DateRangePicker.jsx     # Date range selection
│   │   ├── ServiceTrendChart.jsx   # Per-service trend analysis
│   │   ├── TopServicesChart.jsx    # Top spenders visualization
│   │   ├── TopSpenders.jsx         # Highest cost services table
│   │   └── TotalSpendChart.jsx     # Total spend summary
│   ├── pages/
│   │   ├── Dashboard.jsx           # Main cost overview page
│   │   ├── AnomalyDashboard.jsx    # Anomaly detection view
│   │   ├── BudgetDashboard.jsx     # Budget & burn rate tracking
│   │   ├── ResourceDashboard.jsx   # Resource-level costs
│   │   ├── ResourceTable.jsx       # Resource details table
│   │   └── ServiceBudgets.jsx      # Per-service budget management
│   ├── App.jsx                     # Main app router & navigation
│   ├── App.css                     # Global styles
│   ├── index.css                   # Reset & base styles
│   └── main.jsx                    # React entry point
├── public/                         # Static assets
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── README.md
```

## Installation

### Prerequisites

- Node.js 16+ (recommended 18 LTS)
- npm or yarn

### Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

## Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
# Backend API URL (FastAPI)
VITE_API_URL=http://localhost:8000

# Optional: API timeout (milliseconds)
VITE_API_TIMEOUT=30000
```

**Note**: All environment variables must be prefixed with `VITE_` to be accessible in React.

## Available Scripts

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Run ESLint
npm run lint
```

## Key Pages

### Dashboard.jsx
Main cost overview with:
- Total spend summary
- Cost trends over time
- Top services by cost
- Service-level breakdown

### ServiceBudgets.jsx
Premium budget management interface with:
- 3-column card grid layout
- Color-coded status indicators (healthy/warning/over-budget)
- Real-time budget utilization tracking
- Progress bars for visual reference
- Inline budget editing
- Summary stats

### AnomalyDashboard.jsx
AI-detected cost anomalies:
- IsolationForest detection results
- Trend break identification
- Anomaly impact in USD
- Affected services list

### BudgetDashboard.jsx
Budget and burn rate tracking:
- Month-to-date projections
- Budget vs actual comparison
- Daily burn rate
- Days remaining in month

### ResourceDashboard.jsx
Resource-level cost analysis:
- Individual resource costs
- Resource type breakdown
- Region-based analysis

## API Integration

The frontend communicates with two FastAPI servers:

**Backend API (port 8000)** - Primary
```
GET  /api/costs                    # Costs by service/date
GET  /api/resources                # Resource-level costs
GET  /api/budget/services          # Service budgets
POST /api/budget/services          # Update service budget
GET  /api/budget/services/usage    # Budget utilization
GET  /api/anomalies                # Anomaly detection
```

**App Main (port 8080)** - Secondary
```
GET  /api/budget                   # Budget summary
GET  /api/costs                    # Cost data
```

### Example API Call

```javascript
import axios from "axios";

const api = import.meta.env.VITE_API_URL;

export const getCosts = async (days = 30) => {
  const res = await axios.get(`${api}/api/costs`, { 
    params: { days } 
  });
  return res.data.data;
};
```

## Styling

### Tailwind CSS
- Responsive breakpoints (mobile-first)
- Extended color palette
- Custom spacing scale

### Inline Styles
Complex conditional styling uses inline `style` props with dynamic values.

## Performance Tips

- Code splitting via dynamic imports
- Lazy loading components
- Client-side API response caching
- Proper useEffect dependencies

## Debugging

### Browser DevTools
1. Open F12
2. Go to **Network** tab
3. Watch API calls
4. Check response data format

### Common Issues

**CORS Errors**
- Verify backend is running
- Check `VITE_API_URL` in `.env`
- Backend must have CORS enabled

**Empty Data**
- AWS credentials configured (backend)
- `USE_AWS=true` environment variable
- Date range has valid cost data

## Building for Production

```bash
# Create optimized build
npm run build

# Output: dist/ folder with minified assets

# Test production build
npm run preview
```

Deploy `dist/` to Vercel, Netlify, AWS S3, Docker, or traditional web server.

## Contributing

1. Create feature branch: `git checkout -b feature/description`
2. Make changes in `src/`
3. Test: `npm run dev`
4. Commit: `git commit -m "feat: description"`
5. Push and create PR

## Standards

- **Component Names**: PascalCase
- **Files**: One component per file
- **Styling**: Tailwind CSS classes
- **State**: React hooks (useState, useEffect)

## Troubleshooting

### Port Already in Use
```bash
npx kill-port 5173
npm run dev
```

### Dependency Issues
```bash
rm -r node_modules package-lock.json
npm install
```

### Vite Cache Issues
```bash
rm -r dist node_modules/.vite
npm run build
```

## Resources

- [React Docs](https://react.dev)
- [Vite Guide](https://vitejs.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Recharts](https://recharts.org)
- [Axios](https://axios-http.com)

## License

Part of Cloud Cost AI project.
