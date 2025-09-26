#!/bin/bash

echo "🚀 Setting up React Frontend for Hukuk RAG..."

# Create frontend directory structure
mkdir -p frontend
mkdir -p frontend/src/app
mkdir -p frontend/src/components
mkdir -p frontend/public

cd frontend

# Create package.json if it doesn't exist
if [ ! -f package.json ]; then
    echo "📦 Creating package.json..."
    cat > package.json << 'EOF'
{
  "name": "hukuk-rag-frontend",
  "version": "1.0.0",
  "description": "Modern React frontend for Hukuk RAG API",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "axios": "^1.6.0",
    "lucide-react": "^0.292.0",
    "tailwindcss": "^3.3.5",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31",
    "@tailwindcss/typography": "^0.5.10",
    "clsx": "^2.0.0",
    "react-hot-toast": "^2.4.1",
    "framer-motion": "^10.16.4",
    "react-markdown": "^9.0.1",
    "react-syntax-highlighter": "^15.5.0"
  },
  "devDependencies": {
    "@types/node": "^20.8.7",
    "@types/react": "^18.2.31",
    "@types/react-dom": "^18.2.14",
    "eslint": "^8.52.0",
    "eslint-config-next": "14.0.0",
    "typescript": "^5.2.2"
  }
}
EOF
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create PostCSS config
cat > postcss.config.js << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF

# Create TypeScript config
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
EOF

# Create environment file
cat > .env.local << 'EOF'
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Development settings
NODE_ENV=development
EOF

echo "✅ Frontend setup complete!"
echo ""
echo "🔧 To start the development server:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "🌐 The app will be available at:"
echo "   http://localhost:3000"
echo ""
echo "⚠️  Make sure your API is running on port 8000 before starting the frontend!"

cd ..