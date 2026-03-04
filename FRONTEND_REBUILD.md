# Frontend Rebuild Instructions - Vite + Tailwind v4

## 🧹 Step-by-Step Clean Rebuild

Run these commands IN ORDER:

### 1. Delete the old Next.js frontend
```bash
cd /Users/carlosdiego.ramirez/mydevs/github/SURA/pySURAnalyzer
rm -rf frontend
```

### 2. Fix npm permissions (if needed)
```bash
sudo chown -R 504:20 "/Users/carlosdiego.ramirez/.npm"
```

### 3. Create fresh Vite project
```bash
npm create vite@latest frontend -- --template react-ts
```
When prompted:
- ✅ Confirm package installation
- ✅ Choose "react-ts" template (should be default)

### 4. Navigate and install base dependencies
```bash
cd frontend
npm install
```

### 5. Install Tailwind CSS v4 with Vite plugin
```bash
npm install tailwindcss@next @tailwindcss/vite@next
```

### 6. Install other dependencies
```bash
npm install react-dropzone zustand
```

### 7. Verify installation
```bash
npm list tailwindcss
# Should show: tailwindcss@4.x.x
```

---

## ✅ After Running These Commands

You'll have a **clean Vite project** with:
- React 18 + TypeScript
- Tailwind CSS v4
- react-dropzone (file upload)
- zustand (state management)

Then **let me know** and I'll configure everything and build the components!

---

## 📝 Note

This creates a **completely fresh** project with:
- ✅ No Next.js code
- ✅ No configuration issues
- ✅ Latest Vite
- ✅ Tailwind v4 properly configured
- ✅ Clean slate to build on

**Ready to go!** 🚀
