#!/bin/bash
# Build script for LLMings release package
# Creates a standalone install directory with all necessary files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="$PROJECT_ROOT/install"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Building LLMings release package...${NC}"

# Clean install directory
echo -e "${YELLOW}Cleaning install directory...${NC}"
rm -rf "$INSTALL_DIR/app"
rm -rf "$INSTALL_DIR/static"
rm -rf "$INSTALL_DIR/venv"
rm -f "$INSTALL_DIR/.deps_installed"

# Build frontend
echo -e "${YELLOW}Building frontend...${NC}"
cd "$PROJECT_ROOT/frontend"
npm run build

# Copy backend app
echo -e "${YELLOW}Copying backend...${NC}"
mkdir -p "$INSTALL_DIR/app"
cp -r "$PROJECT_ROOT/backend/app/"* "$INSTALL_DIR/app/"

# Remove __pycache__ directories
find "$INSTALL_DIR/app" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Copy frontend build
echo -e "${YELLOW}Copying frontend build...${NC}"
mkdir -p "$INSTALL_DIR/static"
cp -r "$PROJECT_ROOT/frontend/dist/"* "$INSTALL_DIR/static/"

# Copy requirements.txt
echo -e "${YELLOW}Copying requirements...${NC}"
cp "$PROJECT_ROOT/backend/requirements.txt" "$INSTALL_DIR/"

# Copy .env.example
echo -e "${YELLOW}Copying environment template...${NC}"
cp "$PROJECT_ROOT/.env.example" "$INSTALL_DIR/"

# Make startup scripts executable
chmod +x "$INSTALL_DIR/start.sh"

# Create version file
VERSION=$(grep '"version"' "$PROJECT_ROOT/package.json" | head -1 | sed 's/.*: "\(.*\)".*/\1/')
echo "$VERSION" > "$INSTALL_DIR/VERSION"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Release package built successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Install directory: $INSTALL_DIR"
echo "Version: $VERSION"
echo ""
echo "To create a distributable archive:"
echo "  cd $PROJECT_ROOT"
echo "  tar -czvf llmings-${VERSION}.tar.gz install/"
echo "  # or for zip:"
echo "  zip -r llmings-${VERSION}.zip install/"
