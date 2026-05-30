// ==========================================================================
// BỘ ĐIỀU KHIỂN GIAO DIỆN CHÍNH (VANILLA JS CONTROLLER) - QHTT SOLVER
// ==========================================================================

// Trạng thái ứng dụng (State)
let theme = 'light';
let inputMethod = 'manual'; // 'manual' | 'structured'

// Hàm hiển thị thông báo cao cấp dạng Toast ở trung tâm màn hình (Premium Centered Overlay)
function showToast(title, message, type = 'error') {
  // Loại bỏ các toast cũ đang hiển thị để tránh chồng chéo
  const oldBackdrops = document.querySelectorAll('.custom-toast-backdrop');
  oldBackdrops.forEach(el => el.remove());

  // 1. Tạo lớp phủ mờ toàn màn hình (Modal Backdrop)
  const backdrop = document.createElement('div');
  backdrop.className = 'custom-toast-backdrop animate-fade-in';
  backdrop.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(15, 23, 42, 0.25);
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: auto;
    opacity: 0;
    transition: opacity 0.3s ease;
  `;

  // 2. Tạo hộp thông báo trung tâm (Centered Modal Alert), to lên 20% so với bản cũ
  const toast = document.createElement('div');
  toast.className = 'custom-premium-toast';
  toast.style.cssText = `
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 1.35rem 1.75rem;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    position: relative;
    width: 90%;
    max-width: 480px;
    transform: scale(0.9);
    opacity: 0;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  `;

  // Thiết lập màu sắc và icon theo từng loại thông báo (To hơn 20%)
  let iconBg = '#fee2e2';
  let iconColor = '#ef4444';
  let iconSvg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
  `;

  if (type === 'success') {
    iconBg = '#dcfce7';
    iconColor = '#22c55e';
    iconSvg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
    `;
  } else if (type === 'info') {
    iconBg = '#dbeafe';
    iconColor = '#3b82f6';
    iconSvg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="16" y2="12"/><line x1="12" x2="12.01" y1="8" y2="8"/></svg>
    `;
  }

  // Khung HTML của Toast: Toàn bộ chữ to lên 20%, loại bỏ nút Đồng ý/Xác nhận hoàn toàn
  toast.innerHTML = `
    <!-- Nội dung chính ghép nhóm icon và chữ -->
    <div style="flex: 1; display: flex; flex-direction: column; gap: 0.5rem; padding-right: 1.25rem;">
      <!-- Dòng tiêu đề chứa cả icon và chữ để căn chỉnh hoàn hảo ngang nhau -->
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        <!-- Icon bên trái (To hơn 20%) -->
        <div style="flex-shrink: 0; width: 34px; height: 34px; border-radius: 50%; background-color: ${iconBg}; color: ${iconColor}; display: flex; align-items: center; justify-content: center;">
          ${iconSvg}
        </div>
        <!-- Tiêu đề -->
        <div style="font-size: 1.05rem; font-weight: 700; color: hsl(var(--text-primary)); font-family: 'Outfit', sans-serif;">
          ${title}
        </div>
      </div>
      
      <!-- Chi tiết thông báo thụt lề ngang bằng với tiêu đề -->
      <div style="font-size: 0.95rem; color: hsl(var(--text-secondary)); line-height: 1.5; white-space: pre-line; padding-left: calc(34px + 0.75rem);">
        ${message}
      </div>
    </div>
    
    <!-- Nút đóng (X) bên phải trên -->
    <button class="toast-close-btn" style="position: absolute; top: 1rem; right: 1rem; background: transparent; border: none; color: hsl(var(--text-muted)); cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 4px; border-radius: 6px; transition: all 0.2s;">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
    </button>
  `;

  // Thêm vào backdrop
  backdrop.appendChild(toast);
  document.body.appendChild(backdrop);

  // Kích hoạt animation xuất hiện
  setTimeout(() => {
    backdrop.style.opacity = '1';
    toast.style.transform = 'scale(1)';
    toast.style.opacity = '1';
  }, 10);

  // Hàm tự hủy đóng toast
  const dismissToast = () => {
    backdrop.style.opacity = '0';
    toast.style.transform = 'scale(0.9)';
    toast.style.opacity = '0';
    setTimeout(() => {
      if (backdrop.parentNode) {
        backdrop.parentNode.removeChild(backdrop);
      }
    }, 300);
  };

  // Lắng nghe sự kiện click đóng
  toast.querySelector('.toast-close-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    dismissToast();
  });

  // Click vào bất kỳ vùng nào ngoài hộp thoại hoặc click trực tiếp lên lớp phủ cũng sẽ tự đóng
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) {
      dismissToast();
    }
  });

  // Tự động đóng sau 7 giây để người dùng kịp đọc nội dung lỗi dài
  const autoDismissTimeout = setTimeout(dismissToast, 7000);

  // Hủy timeout tự đóng nếu người dùng chủ động hover
  toast.addEventListener('mouseenter', () => clearTimeout(autoDismissTimeout));
}

// Bộ chuẩn hóa và định dạng lại đề bài toán QHTT để hỗ trợ cú pháp linh hoạt (dấu phẩy, chấm phẩy, viết liền...)
function parseLineConstraints(line) {
  let parts = line.split(/,(?![0-9])/).map(p => p.trim()).filter(Boolean);
  let constraints = [];
  let pendingVars = [];
  
  for (let part of parts) {
    const hasOp = /<=|>=|=|\b(free|tuyy|tuy-y|tuy\s*y|tự\s*do|tuy\s*y|min|max)\b/i.test(part);
    if (hasOp) {
      if (pendingVars.length > 0) {
        constraints.push(pendingVars.join(", ") + ", " + part);
        pendingVars = [];
      } else {
        constraints.push(part);
      }
    } else {
      pendingVars.push(part);
    }
  }
  
  if (pendingVars.length > 0) {
    constraints.push(pendingVars.join(", "));
  }
  
  return constraints;
}

function formatAndNormalizeLP(text) {
  if (!text) return "";
  
  // Chuẩn hóa khoảng trắng trong các toán tử so sánh (ví dụ: < = thành <=, > = thành >=)
  let cleanedText = text.replace(/<\s*=/g, '<=').replace(/>\s*=/g, '>=');
  
  // Tiền xử lý chuyển subscript thành số thường
  const subMap = {
    '₀':'0', '₁':'1', '₂':'2', '₃':'3', '₄':'4',
    '₅':'5', '₆':'6', '₇':'7', '₈':'8', '₉':'9'
  };
  let processed = cleanedText.split('').map(char => subMap[char] || char).join('');
  
  // Thay thế dấu chấm phẩy ; thành dấu phẩy
  processed = processed.replace(/;/g, ',');
  
  // Tách dòng
  let rawLines = processed.split('\n').map(s => s.trim()).filter(Boolean);
  let allSegments = [];
  for (let line of rawLines) {
    allSegments.push(...parseLineConstraints(line));
  }
  
  let objLine = "";
  let mainConstraints = [];
  let signs = {};
  
  for (let seg of allSegments) {
    let cleanSeg = seg.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    let norm = cleanSeg.toLowerCase().replace(/\s+/g, '');
    
    // 1. Dòng hàm mục tiêu
    if (/\b(min|max)\b/i.test(seg)) {
      let match = seg.match(/\b(min|max)\b\s*(?:[a-z](?:\([a-z\d,\s]*\))?\s*=)?\s*(.*)/i);
      if (match) {
        let type = match[1].toLowerCase();
        let expr = match[2].trim();
        expr = expr.replace(/^\+\s*/, '');
        // Định dạng chuẩn: min -2x1 + x2 (bỏ Z =)
        objLine = `${type} ${expr}`;
      } else {
        objLine = seg;
      }
      continue;
    }
    
    // 2. Ràng buộc dấu
    let isSignConstraint = false;
    if (/^((?:x\d+\s*,\s*)*x\d+)\s*(<=|>=)\s*0$/i.test(seg)) {
      let match = seg.match(/^((?:x\d+\s*,\s*)*x\d+)\s*(<=|>=)\s*0$/i);
      let vars = match[1].split(',').map(v => v.trim()).filter(Boolean);
      let op = match[2];
      let type = op === '>=' ? 'pos' : 'neg';
      for (let v of vars) {
        signs[v] = type;
      }
      isSignConstraint = true;
    } else if (/^((?:x\d+,?)+)(free|tuyy|tuy-y|tuy\s*y|tudo)$/i.test(norm)) {
      let match = norm.match(/^((?:x\d+,?)+)(free|tuyy|tuy-y|tuy\s*y|tudo)$/i);
      let vars = match[1].split(',').map(v => v.trim()).filter(Boolean);
      for (let v of vars) {
        signs[v] = 'free';
      }
      isSignConstraint = true;
    }
    
    if (!isSignConstraint) {
      // Chuẩn hóa định dạng khoảng trắng cho các ràng buộc thông thường
      let formattedSeg = seg
        .replace(/\s*<=\s*/g, ' <= ')
        .replace(/\s*>=\s*/g, ' >= ')
        .replace(/(?<![<>])\s*=\s*/g, ' = ')
        .replace(/\s*-\s*/g, ' - ')
        .replace(/\s*\+\s*/g, ' + ');
      // Xóa dấu cộng thừa ở đầu
      formattedSeg = formattedSeg.replace(/^\+\s*/, '');
      mainConstraints.push(formattedSeg);
    }
  }
  
  // Tái thiết lập các ràng buộc dấu theo nhóm đẹp đẽ
  let posVars = [];
  let negVars = [];
  let freeVars = [];
  
  const sortVars = (arr) => {
    return arr.sort((a, b) => {
      let numA = parseInt(a.replace(/\D/g, ''));
      let numB = parseInt(b.replace(/\D/g, ''));
      return numA - numB;
    });
  };
  
  for (let v of Object.keys(signs)) {
    let sign = signs[v];
    if (sign === 'pos') posVars.push(v);
    else if (sign === 'neg') negVars.push(v);
    else if (sign === 'free') freeVars.push(v);
  }
  
  let signLines = [];
  if (posVars.length > 0) {
    signLines.push(`${sortVars(posVars).join(', ')} >= 0`);
  }
  if (negVars.length > 0) {
    signLines.push(`${sortVars(negVars).join(', ')} <= 0`);
  }
  if (freeVars.length > 0) {
    signLines.push(`${sortVars(freeVars).join(', ')} tự do`);
  }
  
  let finalLines = [];
  if (objLine) finalLines.push(objLine);
  finalLines.push(...mainConstraints);
  finalLines.push(...signLines);
  
  return finalLines.join('\n');
}

// Bộ kiểm tra cú pháp và lỗi chi tiết của chuỗi phương trình QHTT nhập thủ công
function validateProblemInput(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  
  if (lines.length === 0) {
    return { valid: false, title: "Thông báo", message: "Vui lòng nhập nội dung đề bài toán trước khi giải.", type: "info" };
  }

  // Tiền xử lý chuyển subscript thành số thường để dễ kiểm tra cú pháp
  const subMap = {
    '₀':'0', '₁':'1', '₂':'2', '₃':'3', '₄':'4',
    '₅':'5', '₆':'6', '₇':'7', '₈':'8', '₉':'9'
  };
  const translateSub = (s) => {
    return s.split('').map(char => subMap[char] || char).join('');
  };

  let objLineCount = 0;
  let objLine = null;
  let mainConstraintsCount = 0;

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const normLine = translateSub(rawLine).toLowerCase().replace(/\s+/g, '');

    if (normLine.includes('min') || normLine.includes('max')) {
      objLineCount++;
      objLine = rawLine;
    }
  }

  if (objLineCount === 0) {
    return { valid: false, title: "Lỗi cấu trúc bài toán", message: "Thiếu hàm mục tiêu (dòng chứa 'min' hoặc 'max')!", type: "error" };
  }
  if (objLineCount > 1) {
    return { valid: false, title: "Lỗi cấu trúc bài toán", message: "Bài toán chỉ được phép có duy nhất 1 dòng hàm mục tiêu (chứa 'min' hoặc 'max')!", type: "error" };
  }

  // Kiểm tra chi tiết từng dòng
  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const normLine = translateSub(rawLine).toLowerCase().replace(/\s+/g, '');

    // 1. Kiểm tra dòng hàm mục tiêu
    if (rawLine === objLine) {
      // Hàm mục tiêu phải có ít nhất 1 biến x
      const hasVar = /x\d+/.test(normLine);
      if (!hasVar) {
        return { valid: false, title: "Lỗi cú pháp hàm mục tiêu", message: `Dòng hàm mục tiêu "${rawLine}" bị lỗi cú pháp: Thiếu biểu thức chứa biến (ví dụ: min -x1 + x2)!`, type: "error" };
      }
      continue;
    }

    // 2. Kiểm tra dòng ràng buộc / dấu
    const operators = ['<=', '>=', '=', '<', '>'];
    let foundOp = null;
    for (const op of operators) {
      if (rawLine.includes(op)) {
        foundOp = op;
        break;
      }
    }

    if (foundOp) {
      const parts = rawLine.split(foundOp).map(p => p.trim());
      const lhs = parts[0];
      const rhs = parts[1];

      if (!lhs) {
        return { valid: false, title: "Lỗi cú pháp ràng buộc", message: `Dòng "${rawLine}" bị lỗi cú pháp: Thiếu biểu thức ở vế trái!`, type: "error" };
      }
      if (rhs === undefined || rhs === '') {
        return { valid: false, title: "Lỗi cú pháp ràng buộc", message: `Dòng "${rawLine}" bị lỗi cú pháp: Thiếu giá trị so sánh ở vế phải (ví dụ: >= 0 hoặc <= 6)!`, type: "error" };
      }

      // Kiểm tra vế phải có phải số hợp lệ không
      const cleanRhs = translateSub(rhs).replace(/\s+/g, '');
      const isValidNumber = /^[+-]?\d+(\.\d+)?(\/\d+)?$/.test(cleanRhs);

      // Nếu là ràng buộc dấu (Ví dụ: x1 >= 0, hoặc x1,x2 >= 0)
      const isPureSign = /^(x\d+,?)+$/.test(lhs.replace(/\s+/g, '')) && cleanRhs === '0';

      if (!isPureSign) {
        if (!isValidNumber) {
          return { valid: false, title: "Lỗi cú pháp ràng buộc", message: `Dòng "${rawLine}" có vế phải "${rhs}" không phải là số hợp lệ!`, type: "error" };
        }
        mainConstraintsCount++;
      }
    } else {
      // Không có toán tử so sánh -> kiểm tra xem có phải khai báo free / tùy ý không
      const isFreeDecl = /^(x\d+,?)+(tuyy|free|tuy-y|tuy\s*y)$/i.test(normLine.normalize("NFD").replace(/[\u0300-\u036f]/g, ""));
      if (!isFreeDecl) {
        return { valid: false, title: "Lỗi cú pháp ràng buộc", message: `Dòng "${rawLine}" bị lỗi cú pháp: Thiếu dấu so sánh (<=, >=, =) hoặc từ khóa xác định (free, tùy ý)!`, type: "error" };
      }
    }
  }

  // Nếu chỉ nhập mỗi hàm mục tiêu
  if (mainConstraintsCount === 0) {
    return { valid: false, title: "Lỗi cấu trúc bài toán", message: "Thiếu các dòng ràng buộc chính của bài toán (ví dụ: x1 - 2x2 <= 4)!", type: "error" };
  }

  return { valid: true };
}

// Dữ liệu Form Builder
let formObjective = 'min';
let formVarsCount = 2;
let formObjCoeffs = ['-1', '1'];
let formConstraints = [
  { coeffs: ['-1', '-2'], op: '<=', val: '6' },
  { coeffs: ['1', '-2'], op: '<=', val: '4' },
  { coeffs: ['-1', '1'], op: '<=', val: '1' }
];
let formBounds = [
  { op: '>=', val: '0' }, // x1 >= 0
  { op: '>=', val: '0' }  // x2 >= 0
];

// Các phần tử DOM (DOM Elements)
const themeToggleBtn = document.getElementById('themeToggleBtn');
const themeIcon = document.getElementById('themeIcon');

// Các nút chọn chế độ ban đầu & quay lại & layout containers
const onboardingContainer = document.getElementById('onboardingContainer');
const appHeader = document.getElementById('appHeader');
const appBodyGrid = document.getElementById('appBodyGrid');
const selectManualBtn = document.getElementById('selectManualBtn');
const selectStructuredBtn = document.getElementById('selectStructuredBtn');
const backToMenuBtn = document.getElementById('backToMenuBtn');

const manualInputSection = document.getElementById('manualInputSection');
const structuredInputSection = document.getElementById('structuredInputSection');
const exportPdfBtn = document.getElementById('exportPdfBtn');
const problemTextarea = document.getElementById('problemTextarea');

const formObjectiveSelect = document.getElementById('formObjective');
const formVarsCountInput = document.getElementById('formVarsCount');
const formConsCountInput = document.getElementById('formConsCount');
const objCoeffsContainer = document.getElementById('objCoeffsContainer');
const constraintsContainer = document.getElementById('constraintsContainer');
const boundsContainer = document.getElementById('boundsContainer');
const addConstraintRowBtn = document.getElementById('addConstraintRowBtn');
const compiledPreviewBox = document.getElementById('compiledPreviewBox');

const solveBtn = document.getElementById('solveBtn');
const solveBtnText = document.getElementById('solveBtnText');
const solveIconPlay = document.getElementById('solveIconPlay');
const solveIconSpin = document.getElementById('solveIconSpin');

const resultTabBtnSteps = document.getElementById('resultTabBtnSteps');
const resultTabBtnGraph = document.getElementById('resultTabBtnGraph');

const emptyState = document.getElementById('emptyState');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const errorText = document.getElementById('errorText');
const stepsTabContent = document.getElementById('stepsTabContent');
const graphTabContent = document.getElementById('graphTabContent');

const solutionStatusHeader = document.getElementById('solutionStatusHeader');
const simplexOutputCode = document.getElementById('simplexOutputCode');
const geometricGraphImage = document.getElementById('geometricGraphImage');
const geomGraphZoomContainer = document.getElementById('geomGraphZoomContainer');

// Các nút tương tác khảo sát đồ thị & lời giải hình học
const geomPromptGraphBox = document.getElementById('geomPromptGraphBox');
const showGeomGraphBtn = document.getElementById('showGeomGraphBtn');
const geomGraphDisplaySection = document.getElementById('geomGraphDisplaySection');
const geomPromptSolutionBox = document.getElementById('geomPromptSolutionBox');
const showGeomSolutionBtn = document.getElementById('showGeomSolutionBtn');
const geomSolutionDisplaySection = document.getElementById('geomSolutionDisplaySection');
const geometricSolutionStepsBox = document.getElementById('geometricSolutionStepsBox');

// Các phần tử tương tác khảo sát lời giải chi tiết Đơn hình
const simplexConclusionBox = document.getElementById('simplexConclusionBox');
const simplexConclusionText = document.getElementById('simplexConclusionText');
const simplexPromptStepsBox = document.getElementById('simplexPromptStepsBox');
const showSimplexStepsBtn = document.getElementById('showSimplexStepsBtn');
const hideSimplexStepsPromptBtn = document.getElementById('hideSimplexStepsPromptBtn');
const simplexStepsDisplaySection = document.getElementById('simplexStepsDisplaySection');
const simplexPrintOutputCode = document.getElementById('simplexPrintOutputCode');

// Biến lưu trữ text giải thuật hình học
let geomStepsText = '';

// Các phần tử tương tác in ấn PDF
const printConfigModal = document.getElementById('printConfigModal');
const printOptSimplex = document.getElementById('printOptSimplex');
const printOptSimplexWrapper = document.getElementById('printOptSimplexWrapper');
const printOptBland = document.getElementById('printOptBland');
const printOptBlandWrapper = document.getElementById('printOptBlandWrapper');
const printOptTwoPhase = document.getElementById('printOptTwoPhase');
const printOptTwoPhaseWrapper = document.getElementById('printOptTwoPhaseWrapper');
const printOptGeom = document.getElementById('printOptGeom');
const printOptGeomWrapper = document.getElementById('printOptGeomWrapper');
const closePrintModalBtn = document.getElementById('closePrintModalBtn');
const confirmPrintBtn = document.getElementById('confirmPrintBtn');
const academicPrintArea = document.getElementById('academicPrintArea');
const printGeomSection = document.getElementById('printGeomSection');
const printGeometricImage = document.getElementById('printGeometricImage');
const printGeomLegendBox = document.getElementById('printGeomLegendBox');
const printSimplexSection = document.getElementById('printSimplexSection');
const printBlandSection = document.getElementById('printBlandSection');
const printTwoPhaseSection = document.getElementById('printTwoPhaseSection');
const printConclusionOnlySection = document.getElementById('printConclusionOnlySection');
const printConclusionOnlyText = document.getElementById('printConclusionOnlyText');

// Biến lưu trữ kết quả giải bài toán gần nhất
let lastSolveResult = null;

// Danh sách các phương pháp đã được giải để hiển thị song song
let solvedMethods = [];

// Trạng thái theo dõi xem người dùng đã bấm xem chi tiết chưa
let stepsViewed = false;
let geomViewed = false;

// Khởi tạo bài toán mẫu mặc định trong textarea để nâng cao trải nghiệm người dùng
problemTextarea.value = `min - x1 + x2
- x1 - 2x2 <= 6
x1 - 2x2 <= 4
- x1 + x2 <= 1
x1 >= 0
x2 >= 0`;

// ==========================================================================
// 1. QUẢN LÝ GIAO DIỆN SÁNG / TỐI (THEME MANAGER)
// ==========================================================================
themeToggleBtn.addEventListener('click', () => {
  if (theme === 'dark') {
    theme = 'light';
    document.documentElement.setAttribute('data-theme', 'light');
    // Đang ở Light Mode -> Hiển thị biểu tượng Moon để đổi sang Dark
    themeIcon.innerHTML = `<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>`;
  } else {
    theme = 'dark';
    document.documentElement.setAttribute('data-theme', 'dark');
    // Đang ở Dark Mode -> Hiển thị biểu tượng Sun để đổi sang Light
    themeIcon.innerHTML = `<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="1" y2="3"/><line x1="12" x2="12" y1="21" y2="23"/><line x1="4.22" x2="5.64" y1="4.22" y2="5.64"/><line x1="18.36" x2="19.78" y1="18.36" y2="19.78"/><line x1="1" x2="3" y1="12" y2="12"/><line x1="21" x2="23" y1="12" y2="12"/><line x1="4.22" x2="5.64" y1="19.78" y2="18.36"/><line x1="18.36" x2="19.78" y1="5.64" y2="4.22"/>`;
  }
});

// Hàm tạo hiệu ứng chuyển cảnh chờ mượt mà giữa các chế độ/hành động (Không hiển thị văn bản)
function showGlobalTransition(callback, duration = 1000) {
  const loader = document.getElementById('globalTransitionLoader');
  
  if (loader) {
    loader.style.display = 'flex';
    
    setTimeout(() => {
      // Thực hiện hành động chính
      if (callback) callback();
      
      // Ẩn loader sau khi hoàn tất hành động
      setTimeout(() => {
        loader.style.display = 'none';
      }, 200); // Khoảng chờ mượt nhỏ để ẩn hẳn
    }, duration);
  } else {
    // Dự phòng nếu không tìm thấy loader
    if (callback) callback();
  }
}

// ==========================================================================
// 2. CHỌN CHẾ ĐỘ BAN ĐẦU & CHUYỂN ĐỔI TAB NHẬP (ONBOARDING & TABS)
// ==========================================================================

// Click nút Nhập thủ công từ màn hình Welcome
selectManualBtn.addEventListener('click', () => {
  showGlobalTransition(() => {
    inputMethod = 'manual';
    onboardingContainer.style.display = 'none';
    document.body.classList.add('has-app-view');
    appHeader.style.display = 'flex';
    appBodyGrid.style.display = 'grid';
    manualInputSection.style.display = 'flex';
    structuredInputSection.style.display = 'none';
  }, 1000);
});

// Click nút Nhập theo Form từ màn hình Welcome
selectStructuredBtn.addEventListener('click', () => {
  showGlobalTransition(() => {
    inputMethod = 'structured';
    onboardingContainer.style.display = 'none';
    document.body.classList.add('has-app-view');
    appHeader.style.display = 'flex';
    appBodyGrid.style.display = 'grid';
    manualInputSection.style.display = 'none';
    structuredInputSection.style.display = 'flex';
    renderFormBuilder();
  }, 1000);
});

// Click nút Quay lại màn hình Welcome
backToMenuBtn.addEventListener('click', () => {
  document.body.classList.remove('has-app-view');
  onboardingContainer.style.display = 'flex';
  appHeader.style.display = 'none';
  appBodyGrid.style.display = 'none';
});

// Quản lý cấu hình in ấn PDF lời giải
exportPdfBtn.addEventListener('click', () => {
  if (!lastSolveResult) return;

  if (!stepsViewed) {
    // Chỉ in kết luận, không hiện modal cấu hình và không in các bước chi tiết
    printGeomSection.style.display = 'none';
    printSimplexSection.style.display = 'none';
    printBlandSection.style.display = 'none';
    printTwoPhaseSection.style.display = 'none';
    
    // Đưa nội dung kết luận vào section kết luận in riêng biệt
    // (simplexConclusionBox bị ẩn bởi CSS @media print nên cần section riêng này)
    const conclusionText = simplexConclusionText ? simplexConclusionText.textContent.trim() : '';
    if (printConclusionOnlySection && printConclusionOnlyText) {
      printConclusionOnlyText.textContent = conclusionText;
      printConclusionOnlySection.style.display = 'block';
    }
    
    window.print();
    return;
  }

  // Khi in có lời giải, ẩn section kết luận đơn độc (kết luận đã có cuối lời giải rồi)
  if (printConclusionOnlySection) {
    printConclusionOnlySection.style.display = 'none';
  }

  // 1. Kiểm tra Phương pháp Đơn hình thường
  if (solvedMethods.includes('simplex')) {
    printOptSimplexWrapper.style.display = 'flex';
    printOptSimplex.checked = true;
  } else {
    printOptSimplexWrapper.style.display = 'none';
    printOptSimplex.checked = false;
  }

  // 2. Kiểm tra Phương pháp Bland
  if (solvedMethods.includes('bland')) {
    printOptBlandWrapper.style.display = 'flex';
    printOptBland.checked = true;
  } else {
    printOptBlandWrapper.style.display = 'none';
    printOptBland.checked = false;
  }

  // 3. Kiểm tra Phương pháp Đơn hình 2 pha
  if (solvedMethods.includes('two_phase')) {
    printOptTwoPhaseWrapper.style.display = 'flex';
    printOptTwoPhase.checked = true;
  } else {
    printOptTwoPhaseWrapper.style.display = 'none';
    printOptTwoPhase.checked = false;
  }

  // 4. Kiểm tra Phương pháp Hình học
  if (lastSolveResult.has_graph && geomViewed) {
    printOptGeomWrapper.style.display = 'flex';
    printOptGeom.checked = true;
  } else {
    printOptGeomWrapper.style.display = 'none';
    printOptGeom.checked = false;
  }

  // Luôn hiển thị Modal để người dùng chọn in các phương pháp đã giải quyết
  printConfigModal.style.display = 'flex';
});

// Click Hủy trên Modal cấu hình in
closePrintModalBtn.addEventListener('click', () => {
  printConfigModal.style.display = 'none';
});

// Click Xác nhận in trên Modal
confirmPrintBtn.addEventListener('click', () => {
  const printSimplex = printOptSimplex.checked;
  const printBland = printOptBland.checked;
  const printTwoPhase = printOptTwoPhase.checked;
  const printGeom = printOptGeom.checked;

  if (!printSimplex && !printBland && !printTwoPhase && !printGeom) {
    alert("Vui lòng chọn ít nhất một thành phần lời giải để in!");
    return;
  }

  printConfigModal.style.display = 'none';

  // 1. Thu thập các phân đoạn lời giải hiển thị thực tế khi in
  const visibleSections = [];
  
  if (printGeom && lastSolveResult && lastSolveResult.has_graph) {
    visibleSections.push(printGeomSection);
    
    // Copy legend chú giải từ màn hình sang bản in
    const legendBox = document.getElementById('geomGraphLegendBox');
    if (legendBox) {
      printGeomLegendBox.innerHTML = legendBox.innerHTML;
    } else {
      printGeomLegendBox.innerHTML = '';
    }
  }

  if (printSimplex && solvedMethods.includes('simplex')) {
    visibleSections.push(printSimplexSection);
  }

  if (printBland && solvedMethods.includes('bland')) {
    visibleSections.push(printBlandSection);
  }

  if (printTwoPhase && solvedMethods.includes('two_phase')) {
    visibleSections.push(printTwoPhaseSection);
  }

  // 2. Ẩn tất cả phân đoạn in mặc định
  printGeomSection.style.display = 'none';
  printSimplexSection.style.display = 'none';
  printBlandSection.style.display = 'none';
  printTwoPhaseSection.style.display = 'none';

  // 3. Hiển thị các phần được chọn in và tự động chèn ngắt trang (page break) chuẩn xác từ phần thứ hai trở đi
  visibleSections.forEach((sec, idx) => {
    sec.style.display = (sec === printGeomSection) ? 'flex' : 'block';
    if (idx > 0) {
      sec.style.setProperty('page-break-before', 'always', 'important');
      sec.style.setProperty('break-before', 'page', 'important');
    } else {
      sec.style.setProperty('page-break-before', 'avoid', 'important');
      sec.style.setProperty('break-before', 'avoid', 'important');
    }
  });

  // Kích hoạt lệnh in của trình duyệt sau khi hình ảnh đã tải xong hoàn toàn (nếu in hình học)
  if (printGeom && lastSolveResult && lastSolveResult.has_graph) {
    const canvas = document.getElementById('geomCanvas');
    if (canvas) {
      printGeometricImage.onload = () => {
        setTimeout(() => {
          window.print();
          printGeometricImage.onload = null; // Gỡ bỏ listener tránh kích hoạt chéo
        }, 250); // Trì hoãn 250ms để trình duyệt hoàn tất việc giải mã (decode) và kết xuất (render) đồ thị lên trang in
      };
      printGeometricImage.src = canvas.toDataURL('image/png');
    } else {
      window.print();
    }
  } else {
    window.print();
  }
});

// ==========================================================================
// 3. ĐỘNG HÓA BỘ BIÊN SOẠN FORM (FORM BUILDER ENGINE)
// ==========================================================================

// Hàm dịch Form Builder sang Text đề bài tiêu chuẩn
function compileFormToText() {
  let lines = [];
  
  // 1. Hàm mục tiêu
  let objTerms = [];
  for (let i = 0; i < formVarsCount; i++) {
    const val = parseFloat(formObjCoeffs[i]);
    if (isNaN(val) || val === 0) continue;
    const sign = val > 0 ? '+' : '-';
    const absVal = Math.abs(val);
    const coeffStr = absVal === 1 ? '' : absVal.toString();
    objTerms.push(`${sign} ${coeffStr}x${i + 1}`);
  }
  let objTermsStr = objTerms.join(' ').replace(/^\+\s*/, '').trim();
  lines.push(`${formObjective} ${objTermsStr || '0'}`);
  
  // 2. Các ràng buộc hệ số
  formConstraints.forEach(c => {
    let terms = [];
    for (let i = 0; i < formVarsCount; i++) {
      const num = parseFloat(c.coeffs[i]);
      if (isNaN(num) || num === 0) continue;
      const sign = num > 0 ? '+' : '-';
      const absVal = Math.abs(num);
      const coeffStr = absVal === 1 ? '' : absVal.toString();
      terms.push(`${sign} ${coeffStr}x${i + 1}`);
    }
    let termsStr = terms.join(' ').replace(/^\+\s*/, '').trim();
    lines.push(`${termsStr || '0'} ${c.op} ${c.val || '0'}`);
  });
  
  // 3. Ràng buộc dấu của từng biến
  for (let i = 0; i < formVarsCount; i++) {
    const b = formBounds[i] || { op: '>=', val: '0' };
    if (b.op === 'free') {
      lines.push(`x${i+1} free`);
    } else {
      lines.push(`x${i+1} ${b.op} ${b.val || '0'}`);
    }
  }
  
  return lines.join('\n');
}

// Cập nhật hộp xem trước toán bản dịch
function updateCompiledPreview() {
  const text = compileFormToText();
  compiledPreviewBox.textContent = text;
}

// Render động toàn bộ Form
function renderFormBuilder() {
  // Đồng bộ số lượng ràng buộc vào ô nhập số lượng ràng buộc
  if (formConsCountInput) {
    formConsCountInput.value = formConstraints.length;
  }

  // A. Render hệ số hàm mục tiêu
  let objHtml = '';
  for (let i = 0; i < formVarsCount; i++) {
    if (i > 0) objHtml += `<span style="color: hsl(var(--text-muted)); font-size: 0.85rem; font-weight: 500;">+</span>`;
    objHtml += `
      <div style="display: flex; align-items: center; gap: 0.25rem;">
        <input type="text" class="input-number-field obj-coeff-input" data-index="${i}" value="${formObjCoeffs[i] || '0'}">
        <span class="builder-var-label">x<sub>${i+1}</sub></span>
      </div>`;
  }
  objCoeffsContainer.innerHTML = objHtml;

  // B. Render các hàng ràng buộc
  let constrHtml = '';
  formConstraints.forEach((constraint, cIdx) => {
    let coeffsHtml = '';
    for (let vIdx = 0; vIdx < formVarsCount; vIdx++) {
      if (vIdx > 0) coeffsHtml += `<span style="color: hsl(var(--text-muted)); font-size: 0.75rem;">+</span>`;
      coeffsHtml += `
        <div style="display: flex; align-items: center; gap: 0.15rem;">
          <input type="text" class="input-number-field const-coeff-input" data-c-idx="${cIdx}" data-v-idx="${vIdx}" style="width: 45px; padding: 0.25rem;" value="${constraint.coeffs[vIdx] || '0'}">
          <span class="builder-var-label" style="font-size: 0.75rem;">x<sub>${vIdx+1}</sub></span>
        </div>`;
    }
    
    constrHtml += `
      <div class="form-builder-row animate-fade-in">
        <div style="display: flex; flex-wrap: wrap; gap: 0.35rem; align-items: center; flex: 1;">
          ${coeffsHtml}
          
          <select class="select-field const-op-select" data-c-idx="${cIdx}" style="padding: 0.2rem 0.35rem; font-size: 0.75rem; width: 55px; height: 26px;">
            <option value="<=" ${constraint.op === '<=' ? 'selected' : ''}>&le;</option>
            <option value=">=" ${constraint.op === '>=' ? 'selected' : ''}>&ge;</option>
            <option value="=" ${constraint.op === '=' ? 'selected' : ''}>=</option>
          </select>

          <input type="text" class="input-number-field const-val-input" data-c-idx="${cIdx}" style="width: 45px; padding: 0.25rem;" value="${constraint.val || '0'}">
        </div>
        
        <button class="builder-remove-btn const-remove-btn" data-c-idx="${cIdx}" title="Xóa ràng buộc này">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
        </button>
      </div>`;
  });
  constraintsContainer.innerHTML = constrHtml || `<div style="font-size: 0.8rem; color: hsl(var(--text-muted)); font-style: italic; padding: 0.5rem 0;">Chưa có điều kiện ràng buộc. Hãy click thêm ràng buộc.</div>`;

  // C. Render ràng buộc dấu
  let boundsHtml = '';
  for (let i = 0; i < formVarsCount; i++) {
    const bound = formBounds[i] || { op: '>=', val: '0' };
    boundsHtml += `
      <div style="display: flex; align-items: center; gap: 0.35rem; background: hsla(var(--bg-primary) / 0.2); padding: 0.35rem 0.5rem; border-radius: 4px; border: 1px solid var(--glass-border);">
        <span class="builder-var-label" style="font-size: 0.8rem;">x<sub>${i+1}</sub></span>
        <select class="select-field bound-op-select" data-b-idx="${i}" style="padding: 0.15rem 0.35rem; font-size: 0.75rem; width: 60px; height: 24px;">
          <option value=">=" ${bound.op === '>=' ? 'selected' : ''}>&ge;</option>
          <option value="<=" ${bound.op === '<=' ? 'selected' : ''}>&le;</option>
          <option value="free" ${bound.op === 'free' ? 'selected' : ''}>Tự do</option>
        </select>
        ${bound.op !== 'free' ? `
          <input type="text" class="input-number-field bound-val-input" data-b-idx="${i}" style="width: 30px; padding: 0.15rem; font-size: 0.75rem;" value="${bound.val || '0'}">
        ` : ''}
      </div>`;
  }
  boundsContainer.innerHTML = boundsHtml;

  // Cập nhật lại bản dịch
  updateCompiledPreview();
}

// --------------------------------------------------------------------------
// LẮNG NGHE SỰ KIỆN THAY ĐỔI FORM (EVENT DELEGATION)
// --------------------------------------------------------------------------

// 1. Đổi loại mục tiêu (min/max)
formObjectiveSelect.addEventListener('change', (e) => {
  formObjective = e.target.value;
  updateCompiledPreview();
});

// 2. Tăng giảm số lượng biến số
formVarsCountInput.addEventListener('change', (e) => {
  const newCount = parseInt(e.target.value);
  if (isNaN(newCount) || newCount < 1 || newCount > 500) return;
  
  formVarsCount = newCount;
  
  // Tinh chỉnh mảng Hệ số Hàm mục tiêu
  if (formObjCoeffs.length < newCount) {
    while (formObjCoeffs.length < newCount) formObjCoeffs.push('0');
  } else {
    formObjCoeffs.splice(newCount);
  }

  // Tinh chỉnh hệ số của các điều kiện ràng buộc
  formConstraints = formConstraints.map(c => {
    let newCoeffs = [...c.coeffs];
    if (newCoeffs.length < newCount) {
      while (newCoeffs.length < newCount) newCoeffs.push('0');
    } else {
      newCoeffs.splice(newCount);
    }
    return { ...c, coeffs: newCoeffs };
  });

  // Tinh chỉnh ràng buộc dấu
  if (formBounds.length < newCount) {
    while (formBounds.length < newCount) {
      formBounds.push({ op: '>=', val: '0' });
    }
  } else {
    formBounds.splice(newCount);
  }

  // Re-render
  renderFormBuilder();
});

// 2b. Tăng giảm số lượng điều kiện ràng buộc trực tiếp bằng số
formConsCountInput.addEventListener('change', (e) => {
  const newCount = parseInt(e.target.value);
  if (isNaN(newCount) || newCount < 0 || newCount > 500) return;
  
  const currentCount = formConstraints.length;
  if (currentCount < newCount) {
    while (formConstraints.length < newCount) {
      const newRowCoeffs = Array(formVarsCount).fill('0');
      formConstraints.push({ coeffs: newRowCoeffs, op: '<=', val: '0' });
    }
  } else if (currentCount > newCount) {
    formConstraints.splice(newCount);
  }

  // Re-render
  renderFormBuilder();
});

// 3. Lắng nghe cập nhật Hệ số Mục tiêu
objCoeffsContainer.addEventListener('input', (e) => {
  if (e.target.classList.contains('obj-coeff-input')) {
    const idx = parseInt(e.target.getAttribute('data-index'));
    formObjCoeffs[idx] = e.target.value;
    updateCompiledPreview();
  }
});

// 4. Lắng nghe cập nhật Hàng Ràng buộc (Coeffs, Operators, values)
constraintsContainer.addEventListener('input', (e) => {
  if (e.target.classList.contains('const-coeff-input')) {
    const cIdx = parseInt(e.target.getAttribute('data-c-idx'));
    const vIdx = parseInt(e.target.getAttribute('data-v-idx'));
    formConstraints[cIdx].coeffs[vIdx] = e.target.value;
    updateCompiledPreview();
  }
  
  if (e.target.classList.contains('const-val-input')) {
    const cIdx = parseInt(e.target.getAttribute('data-c-idx'));
    formConstraints[cIdx].val = e.target.value;
    updateCompiledPreview();
  }
});

constraintsContainer.addEventListener('change', (e) => {
  if (e.target.classList.contains('const-op-select')) {
    const cIdx = parseInt(e.target.getAttribute('data-c-idx'));
    formConstraints[cIdx].op = e.target.value;
    updateCompiledPreview();
  }
});

// Click nút xóa một ràng buộc
constraintsContainer.addEventListener('click', (e) => {
  const removeBtn = e.target.closest('.const-remove-btn');
  if (removeBtn) {
    const cIdx = parseInt(removeBtn.getAttribute('data-c-idx'));
    formConstraints.splice(cIdx, 1);
    renderFormBuilder();
  }
});

// Click nút thêm mới một ràng buộc
addConstraintRowBtn.addEventListener('click', () => {
  const newRowCoeffs = Array(formVarsCount).fill('0');
  formConstraints.push({ coeffs: newRowCoeffs, op: '<=', val: '0' });
  renderFormBuilder();
});

// 5. Lắng nghe cập nhật Ràng buộc dấu
boundsContainer.addEventListener('change', (e) => {
  if (e.target.classList.contains('bound-op-select')) {
    const bIdx = parseInt(e.target.getAttribute('data-b-idx'));
    formBounds[bIdx].op = e.target.value;
    renderFormBuilder(); // Re-render để ẩn/hiện ô nhập số val
  }
});

boundsContainer.addEventListener('input', (e) => {
  if (e.target.classList.contains('bound-val-input')) {
    const bIdx = parseInt(e.target.getAttribute('data-b-idx'));
    formBounds[bIdx].val = e.target.value;
    updateCompiledPreview();
  }
});

// ==========================================================================
// 4. KẾT NỐI API GIẢI TOÁN & TỔ CHỨC TAB KẾT QUẢ (SOLVER PIPELINE & TABS)
// ==========================================================================

// Sự kiện chuyển đổi Tab kết quả
let activeResultTab = 'steps'; // 'steps' | 'graph'

resultTabBtnSteps.addEventListener('click', () => {
  activeResultTab = 'steps';
  resultTabBtnSteps.classList.add('active');
  resultTabBtnGraph.classList.remove('active');
  stepsTabContent.style.display = 'flex';
  graphTabContent.style.display = 'none';
});

resultTabBtnGraph.addEventListener('click', () => {
  activeResultTab = 'graph';
  resultTabBtnGraph.classList.add('active');
  resultTabBtnSteps.classList.remove('active');
  graphTabContent.style.display = 'flex';
  stepsTabContent.style.display = 'none';
});

// Hàm gọi API Solve Quy hoạch tuyến tính
// Hàm gọi API Solve Quy hoạch tuyến tính
async function handleSolveLP(isFromHistory = false, forcedMethod = null, autoExpandSteps = false) {
  // Lấy dữ liệu theo phương thức nhập
  const problemInput = inputMethod === 'manual'
    ? problemTextarea.value.trim()
    : compileFormToText();

  const validation = validateProblemInput(problemInput);
  if (!validation.valid) {
    showToast(validation.title, validation.message, validation.type);
    return;
  }

  const isAlternative = (forcedMethod !== null);

  if (!isAlternative) {
    // 1. Bật trạng thái Loading của giải chính
    solveBtn.disabled = true;
    solveBtnText.textContent = "Đang giải toán...";
    solveIconPlay.style.setProperty('display', 'none', 'important');
    solveIconSpin.style.setProperty('display', 'block', 'important');

    // Ẩn tất cả kết quả cũ
    emptyState.style.display = 'none';
    errorState.style.display = 'none';
    stepsTabContent.style.display = 'none';
    graphTabContent.style.display = 'none';
    resultTabBtnGraph.style.display = 'none';
    exportPdfBtn.style.display = 'none';
    loadingState.style.display = 'flex';

    // Ẩn khối gợi ý phương pháp khác cũ
    const altPromptBox = document.getElementById('alternativeMethodPromptBox');
    if (altPromptBox) altPromptBox.style.display = 'none';
  } else {
    // Nếu giải phương pháp khác (append thêm), chỉ vô hiệu hóa tạm thời các nút để tránh nhấn nhiều lần
    const buttonsContainer = document.getElementById('alternativeButtonsContainer');
    if (buttonsContainer) {
      buttonsContainer.style.opacity = '0.5';
      buttonsContainer.style.pointerEvents = 'none';
    }
  }

  try {
    // Gọi API
    const response = await fetch('/api/solve', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        problem: problemInput,
        method: forcedMethod
      }),
    });

    const data = await response.json();

    if (!response.ok || data.status === 'error') {
      throw new Error(data.message || 'Lỗi hệ thống khi giải toán.');
    }

    lastSolveResult = data;

    if (!isAlternative) {
      solvedMethods = [data.method];
      
      const additionalSolutionsContainer = document.getElementById('additionalSolutionsContainer');
      if (additionalSolutionsContainer) {
        additionalSolutionsContainer.innerHTML = '';
      }

      // Lưu bài toán giải thành công vào danh sách lịch sử (chỉ khi không gọi từ lịch sử)
      if (!isFromHistory) {
        saveToHistory(problemInput);
      }
      
      stepsViewed = false; // Reset trạng thái xem chi tiết
      geomViewed = false;  // Reset trạng thái xem hình học

      // 2. Hiển thị kết quả thành công
      loadingState.style.display = 'none';
      stepsTabContent.style.display = 'flex';
      exportPdfBtn.style.display = 'flex';
      activeResultTab = 'steps';
      resultTabBtnSteps.classList.add('active');
      resultTabBtnGraph.classList.remove('active');

      solutionStatusHeader.textContent = `Giải thành công! Trạng thái tối ưu: ${data.solver_status || 'Hoàn thành'}`;
      
      // Phân tách Kết luận và các bước lập bảng từ vựng đơn hình
      const rawOutput = data.output_steps || "";
      let stepsPart = rawOutput;
      let conclusionPart = "";

      let conclusionIndex = rawOutput.indexOf("Kết luận:");
      if (conclusionIndex === -1) {
        conclusionIndex = rawOutput.indexOf("kết luận:");
      }

      if (conclusionIndex !== -1) {
        stepsPart = rawOutput.substring(0, conclusionIndex).trim();
        conclusionPart = rawOutput.substring(conclusionIndex + 9).trim(); // 9 là độ dài của "Kết luận:"
      } else {
        conclusionPart = "Hoàn thành giải thuật đơn hình.";
      }

      simplexConclusionText.textContent = conclusionPart.trim();
      simplexOutputCode.textContent = stepsPart.trim();
      
      // Phân tách lời giải đơn hình thành các bước nhỏ học thuật để tránh lỗi ngắt trang (page-break-inside)
      const printBlocks = rawOutput.split(/(?=\b(?:Pha 1:|Pha 2:|Bài toán bổ trợ:|Từ vựng xuất phát:|Từ vựng thứ \d+:|=> Từ vựng|Cho x₀ = 0|Kết luận:))/g)
                                   .map(b => b.trim())
                                   .filter(b => b.length > 0);

      // Xóa sạch nội dung cũ trong tất cả 3 phân đoạn in ấn đơn hình
      printSimplexSection.innerHTML = '';
      printBlandSection.innerHTML = '';
      printTwoPhaseSection.innerHTML = '';

      // Đưa các bước in vào phân đoạn in ấn tương ứng với phương pháp chạy chính ban đầu
      let activePrintSection = printSimplexSection;
      if (data.method === 'bland') activePrintSection = printBlandSection;
      else if (data.method === 'two_phase') activePrintSection = printTwoPhaseSection;

      const pre = document.createElement('pre');
      pre.className = 'simplex-step-block-merged';
      pre.textContent = rawOutput.trim();
      activePrintSection.appendChild(pre);

      // Thiết lập trạng thái khảo sát lời giải chi tiết Đơn hình (mở rộng nếu autoExpandSteps là true)
      if (autoExpandSteps) {
        simplexPromptStepsBox.style.display = 'none';
        simplexStepsDisplaySection.style.display = 'block';
      } else {
        simplexPromptStepsBox.style.display = 'flex';
        simplexStepsDisplaySection.style.display = 'none';
      }
      
      if (data.has_graph) {
        showGeomGraphBtn.onclick = () => {
          geomPromptGraphBox.style.display = 'none';
          geomGraphDisplaySection.style.display = 'flex';
          if (window.currentGraph) {
            window.currentGraph.resizeCanvas();
            window.currentGraph.fitToData();
            window.currentGraph.needsRedraw = true;
          }
          geomViewed = true;
          if (typeof checkAllViewed === 'function') checkAllViewed();
        };
      }
    } else {
      // Xử lý khi giải PHƯƠNG PHÁP PHỤ (Append thêm)
      // 1. Phục hồi trạng thái nút bấm chuyển đổi
      const buttonsContainer = document.getElementById('alternativeButtonsContainer');
      if (buttonsContainer) {
        buttonsContainer.style.opacity = '1';
        buttonsContainer.style.pointerEvents = 'auto';
      }

      const rawOutput = data.output_steps || "";
      let stepsPart = rawOutput;
      
      let conclusionIndex = rawOutput.indexOf("Kết luận:");
      if (conclusionIndex === -1) {
        conclusionIndex = rawOutput.indexOf("kết luận:");
      }
      if (conclusionIndex !== -1) {
        stepsPart = rawOutput.substring(0, conclusionIndex).trim();
      }

      // 2. Tạo card kết quả mới (chỉ chứa các bước giải chi tiết, không lặp lại tiêu đề và kết luận trùng lặp)
      const card = document.createElement('div');
      card.className = 'glass-panel animate-fade-in simplex-screen-only';
      card.style.cssText = "padding: 2rem; display: flex; flex-direction: column; gap: 0.75rem; width: 100%; margin-top: 1rem;";
      
      card.innerHTML = `
        <div style="font-size: 0.9rem; font-weight: 700; color: #bd162c; margin-bottom: -0.25rem; font-family: 'Outfit', sans-serif; text-transform: uppercase;">
          Các bước giải chi tiết:
        </div>
        <pre class="simplex-output" style="border: none; background: transparent; padding: 0; margin: 0; box-shadow: none; white-space: pre-wrap; color: hsl(var(--text-primary)); font-family: 'Consolas', monospace; font-size: 12pt; line-height: 1.45;">${stepsPart.trim()}</pre>
      `;
      
      const additionalSolutionsContainer = document.getElementById('additionalSolutionsContainer');
      if (additionalSolutionsContainer) {
        additionalSolutionsContainer.appendChild(card);
      }

      // 3. Đưa các bước in vào phân đoạn in ấn tương ứng phục vụ PDF
      let activePrintSection = printSimplexSection;
      if (forcedMethod === 'bland') activePrintSection = printBlandSection;
      else if (forcedMethod === 'two_phase') activePrintSection = printTwoPhaseSection;

      activePrintSection.innerHTML = ''; // Đảm bảo làm sạch phân đoạn phụ trước khi render

      const pre = document.createElement('pre');
      pre.className = 'simplex-step-block-merged';
      pre.textContent = stepsPart.trim();
      activePrintSection.appendChild(pre);

      // 4. Đẩy phương pháp phụ vào danh sách đã giải
      solvedMethods.push(forcedMethod);
    }

    // Hiển thị khối gợi ý phương pháp giải thay thế
    renderAlternativeMethodPrompt();

    // Kiểm tra và hiển thị phần Đồ thị (nằm ngay dưới phần Đơn hình)
    if (data.has_graph) {
      graphTabContent.style.display = 'flex';
      
      // Khởi tạo đồ thị Client-side với HTML5 Canvas
      if (window.currentGraph) {
        window.currentGraph.destroy();
      }
      if (data.graph_data) {
        window.currentGraph = new window.DesmosGraph('geomCanvas', data.graph_data);
      }
      
      // Render dynamic legend under the image
      let legendBox = document.getElementById('geomGraphLegendBox');
      if (legendBox) {
        const rawGeomOutputNormalized = (data.geom_steps || "").replace(/\r\n/g, '\n');
        let constraints = [];
        const matchLine = /Ta gán các số thứ tự cho các ràng buộc:([\s\S]*?)(?=\n\n|\n[A-Z]|\n=[=-]|$)/i;
        const matchBlock = rawGeomOutputNormalized.match(matchLine);
        if (matchBlock) {
          const lines = matchBlock[1].split('\n');
          lines.forEach(line => {
            const itemMatch = line.match(/^\s*(.*?)\s+\((\d+)\)\s*$/);
            if (itemMatch) {
              constraints.push({
                index: itemMatch[2],
                expr: itemMatch[1].trim()
              });
            }
          });
        }

        // Tự động xác định màu sắc hiển thị đồng bộ với Matplotlib Tab10
        const palette = ["#1f77b4", "#2ca02c", "#8c564b", "#9467bd", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"];
        
        let constraintsHtml = '';
        constraints.forEach((c, idx) => {
          let color = '#000000'; // Mặc định đen cho ràng buộc dấu phi âm
          const exprClean = c.expr.replace(/\s+/g, '');
          const isX1Bound = exprClean.includes('x1') || exprClean.includes('x₁');
          const isX2Bound = exprClean.includes('x2') || exprClean.includes('x₂');
          const isZeroVal = exprClean.includes('0') || exprClean.includes('₀') || exprClean.includes('o') || exprClean.includes('O');
          
          const isCoordinateAxis = (isX1Bound && !isX2Bound && isZeroVal) || (isX2Bound && !isX1Bound && isZeroVal);

          if (!isCoordinateAxis) {
            const colorIdx = idx % palette.length;
            color = palette[colorIdx];
          }

          constraintsHtml += `
            <div style="display: flex; align-items: center; gap: 0.65rem; font-size: 0.85rem; font-weight: 500; color: hsl(var(--text-primary));">
              <span style="display: inline-block; width: 14px; height: 4px; background: ${color}; border-radius: 2px; flex-shrink: 0;"></span>
              <span style="font-family: 'Fira Code', 'Consolas', monospace; font-weight: 600; background: hsla(var(--bg-primary) / 0.5); padding: 0.1rem 0.35rem; border-radius: 4px; border: 1px solid var(--glass-border); white-space: nowrap;">${c.expr}</span>
              <span style="font-family: 'Outfit', sans-serif; font-weight: 700; color: hsl(var(--text-secondary));">(${c.index})</span>
            </div>`;
        });

        // Đọc đề bài để lấy biểu thức hàm mục tiêu z hiển thị cực kỳ đầy đủ và động từ geom_steps
        let z_expr = "z: -x₁ + x₂ = lcm(|-1|, |1|) = 1";
        const zMatch = rawGeomOutputNormalized.match(/Vẽ đường thẳng hàm mục tiêu (z:\s*.*?)\n/i);
        if (zMatch) {
          z_expr = zMatch[1].trim();
        }

        legendBox.innerHTML = `
          <div class="glass-panel animate-fade-in" style="width: 100%; padding: 1.25rem; border-radius: var(--radius-md); background: var(--glass-bg); border: 1px solid var(--glass-border); display: flex; flex-direction: column; gap: 0.65rem; box-shadow: var(--shadow-md); margin-top: 0.5rem; text-align: left;">
            <div style="font-size: 0.95rem; font-weight: 700; color: #bd162c; font-family: 'Outfit', sans-serif; letter-spacing: 0.5px; padding-bottom: 0.2rem;">
              Chú thích:
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 0.55rem; width: 100%;">
              <!-- Các đường ràng buộc -->
              ${constraintsHtml}
              
              <!-- Hàm mục tiêu z -->
              <div style="display: flex; align-items: center; gap: 0.65rem; font-size: 0.85rem; font-weight: 500; color: hsl(var(--text-primary));">
                <span style="display: inline-block; width: 14px; height: 1.5px; border-top: 2px dashed red; flex-shrink: 0;"></span>
                <span style="font-family: 'Fira Code', 'Consolas', monospace; font-weight: 700; color: red; background: hsla(var(--bg-primary) / 0.5); padding: 0.1rem 0.35rem; border-radius: 4px; border: 1px solid var(--glass-border); flex-shrink: 0;">${z_expr}</span>
              </div>
            </div>
            
          </div>`;
      }
      
      // Lưu lại kết quả lời giải hình học
      geomStepsText = data.geom_steps || '';
      
      // Khôi phục trạng thái khảo sát ban đầu của phần Đồ thị
      geomPromptGraphBox.style.display = 'flex';
      geomGraphDisplaySection.style.display = 'none';
      if (geomPromptSolutionBox) geomPromptSolutionBox.style.display = 'flex';
      if (geomSolutionDisplaySection) geomSolutionDisplaySection.style.display = 'none';
      if (geometricSolutionStepsBox) geometricSolutionStepsBox.textContent = '';
    } else {
      graphTabContent.style.display = 'none';
      geomStepsText = '';
    }

  } catch (err) {
    // 3. Hiển thị kết quả lỗi
    loadingState.style.display = 'none';
    errorState.style.display = 'flex';
    exportPdfBtn.style.display = 'none';
    errorText.textContent = err.message;
  } finally {
    // Reset nút Solve
    solveBtn.disabled = false;
    solveBtnText.textContent = "Giải Bài Toán";
    solveIconPlay.style.setProperty('display', 'block', 'important');
    solveIconSpin.style.setProperty('display', 'none', 'important');
  }
}

// Hàm render khối gợi ý phương pháp giải thay thế
function renderAlternativeMethodPrompt() {
  const promptBox = document.getElementById('alternativeMethodPromptBox');
  const promptText = document.getElementById('alternativeMethodPromptText');
  const buttonsContainer = document.getElementById('alternativeButtonsContainer');
  
  if (!promptBox || !promptText || !buttonsContainer) return;
  
  // Tùy theo phương pháp gốc được giải để gợi ý phù hợp
  let allMethods = [];
  if (solvedMethods.includes("two_phase")) {
    allMethods = []; // Không gợi ý gì thêm nếu là bài toán Hai Pha
  } else {
    allMethods = [
      { name: "Phương pháp đơn hình", value: "simplex" },
      { name: "Phương pháp Bland", value: "bland" }
    ];
  }

  const alternatives = allMethods.filter(m => !solvedMethods.includes(m.value));

  if (alternatives.length === 0) {
    promptBox.style.display = 'none';
    return;
  }
  
  // Cập nhật câu hỏi dynamically dựa trên số lượng phương pháp còn lại theo đúng văn phong tiếng Việt
  if (alternatives.length === 2) {
    promptText.textContent = `Bạn có muốn xem thử ${alternatives[0].name} hay ${alternatives[1].name} không?`;
  } else {
    promptText.textContent = `Bạn có muốn xem thử lời giải bằng ${alternatives[0].name} không?`;
  }
  
  // Dựng các nút phương pháp thay thế còn lại
  buttonsContainer.innerHTML = '';
  alternatives.forEach(alt => {
    const btn = document.createElement('button');
    btn.style.cssText = "background: #bd162c; color: #ffffff; border-radius: 50px; padding: 0.65rem 2.25rem; font-size: 0.9rem; font-weight: 700; border: none; cursor: pointer; transition: all var(--transition-fast); box-shadow: 0 4px 10px rgba(189, 22, 44, 0.25);";
    btn.textContent = alt.name;
    
    btn.onmouseover = () => { btn.style.background = '#a11022'; };
    btn.onmouseout = () => { btn.style.background = '#bd162c'; };
    
    btn.addEventListener('click', () => {
      // Cập nhật lời giải tại chỗ tức thì (in-place) và tự động hiển thị đầy đủ chi tiết các bước
      handleSolveLP(false, alt.value, true);
    });
    buttonsContainer.appendChild(btn);
  });
  
  if (stepsViewed) {
    promptBox.style.display = 'flex';
  } else {
    promptBox.style.display = 'none';
  }
}

// Lắng nghe sự kiện click giải toán với hiệu ứng chờ chuyển cảnh 1.2 giây
solveBtn.addEventListener('click', () => {
  // Tự động chuẩn hóa và định dạng lại đề bài nếu nhập thủ công trước khi giải và kiểm tra cú pháp
  if (inputMethod === 'manual') {
    try {
      const normalized = formatAndNormalizeLP(problemTextarea.value);
      if (normalized) {
        problemTextarea.value = normalized;
      }
    } catch (e) {
      console.error("Lỗi khi định dạng đề bài:", e);
    }
  }

  // Lấy dữ liệu theo phương thức nhập để kiểm tra lỗi nhập liệu trống trước khi tải
  const problemInput = inputMethod === 'manual'
    ? problemTextarea.value.trim()
    : compileFormToText();

  const validation = validateProblemInput(problemInput);
  if (!validation.valid) {
    showToast(validation.title, validation.message, validation.type);
    return;
  }

  showGlobalTransition(() => {
    handleSolveLP();
  }, 1200);
});

// Khởi tạo trạng thái ban đầu: Chỉ hiển thị bảng chọn chế độ chào mừng
window.addEventListener('load', () => {
  onboardingContainer.style.display = 'flex';
  appHeader.style.display = 'none';
  appBodyGrid.style.display = 'none';
  renderHistory(); // Khởi tạo danh sách lịch sử giải bài đã lưu
});

// ==========================================================================
// 5. TƯƠNG TÁC KHẢO SÁT ĐỒ THỊ & LỜI GIẢI HÌNH HỌC CHI TIẾT
// ==========================================================================
showGeomGraphBtn.addEventListener('click', () => {
  geomViewed = true;
  geomPromptGraphBox.style.display = 'none';
  geomGraphDisplaySection.style.display = 'flex';
});

if (showGeomSolutionBtn) {
  showGeomSolutionBtn.addEventListener('click', () => {
    if (geomPromptSolutionBox) geomPromptSolutionBox.style.display = 'none';
    if (geomSolutionDisplaySection) geomSolutionDisplaySection.style.display = 'flex';
    if (geometricSolutionStepsBox) geometricSolutionStepsBox.textContent = geomStepsText;
  });
}

// Sự kiện nhấn xem Lời giải chi tiết Đơn hình
showSimplexStepsBtn.addEventListener('click', () => {
  stepsViewed = true;
  simplexPromptStepsBox.style.display = 'none';
  simplexStepsDisplaySection.style.display = 'flex';
  
  renderAlternativeMethodPrompt();
  if (lastSolveResult && lastSolveResult.has_graph) {
    graphTabContent.style.display = 'flex';
  }
});

// Sự kiện nhấn "Không" xem chi tiết Đơn hình (ẩn hộp gợi ý)
hideSimplexStepsPromptBtn.addEventListener('click', () => {
  simplexPromptStepsBox.style.display = 'none';
});

// ==========================================================================
// BỘ QUẢN LÝ LỊCH SỬ LÀM BÀI (LOCAL STORAGE HISTORY CONTROLLER)
// ==========================================================================
const historyListContainer = document.getElementById('historyListContainer');
const historySearchInput = document.getElementById('historySearchInput');
const clearAllHistoryBtn = document.getElementById('clearAllHistoryBtn');

// Đọc lịch sử giải bài từ localStorage
function getHistory() {
  try {
    const raw = localStorage.getItem('qhtt_history');
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

// Lưu lịch sử giải bài mới
function saveToHistory(problemInput) {
  if (!problemInput) return;
  const history = getHistory();
  const cleanedInput = problemInput.trim();

  // Kiểm tra trùng lặp đề bài
  const dupIdx = history.findIndex(item => item.problemText.trim() === cleanedInput);
  if (dupIdx !== -1) {
    // Nếu trùng, đưa lên đầu danh sách và cập nhật các trường thông tin đầy đủ để nâng cấp dữ liệu cũ
    const dupItem = history.splice(dupIdx, 1)[0];
    dupItem.timestamp = getFormattedDateTime();
    
    const lines = cleanedInput.split('\n').map(l => l.trim()).filter(Boolean);
    dupItem.title = lines[0] || 'Bài toán QHTT';
    dupItem.preview = lines.slice(1).join(', ');
    dupItem.inputMethod = inputMethod;
    dupItem.problemText = cleanedInput;
    if (inputMethod === 'structured') {
      dupItem.structuredData = {
        formObjective,
        formVarsCount,
        formObjCoeffs: [...formObjCoeffs],
        formConstraints: JSON.parse(JSON.stringify(formConstraints)),
        formBounds: JSON.parse(JSON.stringify(formBounds))
      };
    }
    history.unshift(dupItem);
  } else {
    // Nếu không trùng, thêm mới vào đầu
    const lines = cleanedInput.split('\n').map(l => l.trim()).filter(Boolean);
    const title = lines[0] || 'Bài toán QHTT';
    const constraintsPreview = lines.slice(1).join(', ');

    const newItem = {
      id: Date.now(),
      timestamp: getFormattedDateTime(),
      inputMethod: inputMethod,
      problemText: cleanedInput,
      title: title,
      preview: constraintsPreview,
      // Nếu là structured, lưu trữ lại cấu trúc form để phục hồi hoàn hảo
      structuredData: inputMethod === 'structured' ? {
        formObjective,
        formVarsCount,
        formObjCoeffs: [...formObjCoeffs],
        formConstraints: JSON.parse(JSON.stringify(formConstraints)),
        formBounds: JSON.parse(JSON.stringify(formBounds))
      } : null
    };

    history.unshift(newItem);
  }

  // Giới hạn tối đa 30 bài trong lịch sử
  if (history.length > 30) {
    history.pop();
  }

  localStorage.setItem('qhtt_history', JSON.stringify(history));
  renderHistory();
}

// Lấy chuỗi thời gian định dạng DD/MM hh:mm:ss
function getFormattedDateTime() {
  const now = new Date();
  const dd = String(now.getDate()).padStart(2, '0');
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const hh = String(now.getHours()).padStart(2, '0');
  const min = String(now.getMinutes()).padStart(2, '0');
  const ss = String(now.getSeconds()).padStart(2, '0');
  return `${dd}/${mm} ${hh}:${min}:${ss}`;
}

// Xóa một mục cụ thể khỏi lịch sử
function deleteHistoryItem(id, event) {
  if (event) event.stopPropagation(); // Tránh kích hoạt sự kiện click của thẻ cha
  let history = getHistory();
  history = history.filter(item => item.id !== id);
  localStorage.setItem('qhtt_history', JSON.stringify(history));
  renderHistory();
}

// Xóa toàn bộ lịch sử
function clearAllHistory() {
  if (confirm("Bạn có chắc chắn muốn xóa toàn bộ lịch sử làm bài?")) {
    localStorage.removeItem('qhtt_history');
    renderHistory();
  }
}

// Phục hồi và giải bài toán từ lịch sử
function loadHistoryItem(id) {
  const history = getHistory();
  const item = history.find(item => item.id === id);
  if (!item) return;

  showGlobalTransition(() => {
    // 1. Phục hồi chế độ nhập
    inputMethod = item.inputMethod;
    
    if (inputMethod === 'manual') {
      problemTextarea.value = item.problemText;
      manualInputSection.style.display = 'flex';
      structuredInputSection.style.display = 'none';
    } else {
      // Phục hồi toàn bộ dữ liệu Form Builder
      const sd = item.structuredData;
      if (sd) {
        formObjective = sd.formObjective;
        formVarsCount = sd.formVarsCount;
        formObjCoeffs = [...sd.formObjCoeffs];
        formConstraints = JSON.parse(JSON.stringify(sd.formConstraints));
        formBounds = JSON.parse(JSON.stringify(sd.formBounds));

        // Cập nhật lại các trường select/input trên giao diện
        formObjectiveSelect.value = formObjective;
        formVarsCountInput.value = formVarsCount;
        formConsCountInput.value = formConstraints.length;

        // Render lại bộ dựng Form
        renderFormBuilder();
      }
      manualInputSection.style.display = 'none';
      structuredInputSection.style.display = 'flex';
    }

    // 2. Kích hoạt giải bài toán (truyền tham số true để giữ nguyên thời gian lịch sử)
    handleSolveLP(true);
  }, 1000);
}

// Render danh sách lịch sử ra giao diện (kèm bộ lọc tìm kiếm)
function renderHistory() {
  const history = getHistory();
  const filterText = historySearchInput.value.trim().toLowerCase();

  const filtered = history.filter(item => {
    return (item.problemText || '').toLowerCase().includes(filterText) ||
           (item.timestamp || '').toLowerCase().includes(filterText);
  });

  if (filtered.length === 0) {
    historyListContainer.innerHTML = `
      <div style="text-align: center; color: hsl(var(--text-muted)); font-size: 0.78rem; padding: 1.5rem 0; width: 100%;">
        ${filterText ? 'Không tìm thấy kết quả phù hợp.' : 'Chưa có lịch sử làm bài.'}
      </div>`;
    return;
  }

  let html = '';
  filtered.forEach(item => {
    const badgeText = item.inputMethod === 'manual' ? 'Thủ công' : 'Nhập giá trị';
    const badgeClass = item.inputMethod === 'manual' ? 'manual' : 'structured';
    
    // Tự động phân tách dòng đề bài để làm fallback hiển thị cho cả các bản ghi cũ
    const lines = (item.problemText || '').split('\n').map(l => l.trim()).filter(Boolean);
    const displayTitle = item.title || lines[0] || 'Bài toán QHTT';
    const displayPreview = item.preview || lines.slice(1).join(', ') || 'Chi tiết bài toán';
    
    html += `
      <div class="history-item" onclick="loadHistoryItem(${item.id})">
        <div class="history-item-header">
          <span>${item.timestamp}</span>
          <button class="history-delete-btn" onclick="deleteHistoryItem(${item.id}, event)" title="Xóa bài này">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
          </button>
        </div>
        <div class="history-item-body">${displayTitle}</div>
        <div class="history-item-footer">
          <div style="font-size: 0.7rem; color: hsl(var(--text-muted)); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 180px;">
            ${displayPreview}
          </div>
          <span class="history-badge ${badgeClass}">${badgeText}</span>
        </div>
      </div>`;
  });

  historyListContainer.innerHTML = html;
}

// Đăng ký sự kiện điều khiển lịch sử
if (historySearchInput) {
  historySearchInput.addEventListener('input', renderHistory);
}
if (clearAllHistoryBtn) {
  clearAllHistoryBtn.addEventListener('click', clearAllHistory);
}


