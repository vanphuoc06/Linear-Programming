class DesmosGraph {
  constructor(canvasId, graphData) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.data = graphData;
    
    // Khởi tạo các giá trị mặc định cho viewport
    this.offsetX = 0;
    this.offsetY = 0;
    this.scale = 50; // pixels per unit
    
    this.isDragging = false;
    this.lastMouseX = 0;
    this.lastMouseY = 0;
    
    this.needsRedraw = true;
    
    // Colors
    this.colors = [
      '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ];
    
    this.resizeCanvas();
    this.fitToData();
    this.setupEvents();
    
    // Bắt đầu vòng lặp render
    this.renderLoop();
  }
  
  resizeCanvas() {
    // Đảm bảo canvas luôn full container và nét trên màn hình Retina
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = `${rect.width}px`;
    this.canvas.style.height = `${rect.height}px`;
    this.ctx.scale(dpr, dpr);
    this.width = rect.width;
    this.height = rect.height;
    this.needsRedraw = true;
  }
  
  fitToData() {
    // Tìm khung bao (bounding box)
    let minX = -1, maxX = 5;
    let minY = -1, maxY = 5;
    
    const points = [];
    if (this.data.vertices && this.data.vertices.length > 0) {
      this.data.vertices.forEach(v => points.push({x: v.x1, y: v.x2}));
    }
    
    // Thêm các giao điểm với trục tọa độ
    if (this.data.constraints) {
      this.data.constraints.forEach(c => {
        if (c.str.replace(/\s+/g, '') === 'x1>=0' || c.str.replace(/\s+/g, '') === 'x2>=0' ||
            c.str.replace(/\s+/g, '') === 'x1<=0' || c.str.replace(/\s+/g, '') === 'x2<=0') {
            return;
        }
        if (Math.abs(c.a) > 1e-7) {
          const xInt = c.c / c.a;
          if (xInt >= -15 && xInt <= 15) points.push({x: xInt, y: 0});
        }
        if (Math.abs(c.b) > 1e-7) {
          const yInt = c.c / c.b;
          if (yInt >= -15 && yInt <= 15) points.push({x: 0, y: yInt});
        }
      });
    }
    
    if (points.length > 0) {
      minX = Math.min(...points.map(p => p.x));
      maxX = Math.max(...points.map(p => p.x));
      minY = Math.min(...points.map(p => p.y));
      maxY = Math.max(...points.map(p => p.y));
    }
    
    const padX = Math.max(3, (maxX - minX) * 0.2);
    const padY = Math.max(3, (maxY - minY) * 0.2);
    
    minX -= padX; maxX += padX;
    minY -= padY; maxY += padY;
    
    const scaleX = this.width / (maxX - minX);
    const scaleY = this.height / (maxY - minY);
    this.scale = Math.min(scaleX, scaleY);
    
    // Căn giữa
    this.offsetX = this.width / 2 - ((minX + maxX) / 2) * this.scale;
    this.offsetY = this.height / 2 + ((minY + maxY) / 2) * this.scale;
    
    this.computeAnnotations();
    
    this.needsRedraw = true;
  }
  
  computeAnnotations() {
      this.annotations = [];
      if (!this.data || !this.width || !this.height) return;

      const minX = this.dataX(0);
      const maxX = this.dataX(this.width);
      const minY = this.dataY(this.height);
      const maxY = this.dataY(0);

      const w_plot = Math.max(1, maxX - minX);
      const h_plot = Math.max(1, maxY - minY);

      const getLineSegmentInBox = (A, B, C, xmin, xmax, ymin, ymax) => {
          let pts = [];
          const eps = 1e-7;
          if (Math.abs(B) > eps) {
              let y = (C - A * xmin) / B;
              if (y >= ymin - eps && y <= ymax + eps) pts.push({x: xmin, y: y});
              y = (C - A * xmax) / B;
              if (y >= ymin - eps && y <= ymax + eps) pts.push({x: xmax, y: y});
          }
          if (Math.abs(A) > eps) {
              let x = (C - B * ymin) / A;
              if (x >= xmin - eps && x <= xmax + eps) pts.push({x: x, y: ymin});
              x = (C - B * ymax) / A;
              if (x >= xmin - eps && x <= xmax + eps) pts.push({x: x, y: ymax});
          }
          let unique = [];
          for (let p of pts) {
              if (!unique.some(u => Math.hypot(p.x - u.x, p.y - u.y) < 1e-4)) {
                  unique.push(p);
              }
          }
          if (unique.length >= 2) return [unique[0], unique[1]];
          return null;
      };

      const isInsideFeasible = (x, y) => {
          if (!this.data || !this.data.constraints) return true;
          for (let c of this.data.constraints) {
              if (['x1>=0', 'x2>=0', 'x1<=0', 'x2<=0'].includes((c.str||"").replace(/\s+/g, ''))) continue;
              let lhs = c.a * x + c.b * y;
              if (c.sign === '<=') { if (lhs > c.c + 1e-6) return false; }
              else if (c.sign === '>=') { if (lhs < c.c - 1e-6) return false; }
              else if (c.sign === '=') { if (Math.abs(lhs - c.c) > 1e-6) return false; }
          }
          if (this.data.signs) {
              if (this.data.signs.x1 === 'pos' && x < -1e-6) return false;
              if (this.data.signs.x1 === 'neg' && x > 1e-6) return false;
              if (this.data.signs.x2 === 'pos' && y < -1e-6) return false;
              if (this.data.signs.x2 === 'neg' && y > 1e-6) return false;
          }
          return true;
      };

      const rectsOverlap = (r1, r2) => {
          return !(r1.x2 < r2.x1 || r1.x1 > r2.x2 || r1.y2 < r2.y1 || r1.y1 > r2.y2);
      };

      // Collect fixed collision boxes (vertices and their labels)
      let collisionBoxes = [];
      if (this.data && this.data.vertices) {
          this.data.vertices.forEach(v => {
              const vx = this.screenX(v.x1);
              const vy = this.screenY(v.x2);
              
              // Vertex point itself (8x8)
              collisionBoxes.push({
                  x1: vx - 8,
                  y1: vy - 8,
                  x2: vx + 8,
                  y2: vy + 8
              });
              
              // Vertex label estimation
              const xStr = v.x1_str || (Number.isInteger(v.x1) ? v.x1 : v.x1.toFixed(2));
              const yStr = v.x2_str || (Number.isInteger(v.x2) ? v.x2 : v.x2.toFixed(2));
              const text = `${v.name}(${xStr}, ${yStr})`;
              const textWidth = text.length * 6.5;
              
              collisionBoxes.push({
                  x1: vx + 6,
                  y1: vy - 18,
                  x2: vx + 6 + textWidth,
                  y2: vy + 2
              });
          });
      }

      if (this.data && this.data.constraints) {
          this.data.constraints.forEach((c, idx) => {
              if (c.sign === '=') return;

              // Expand search slightly outside viewport to allow annotations on boundary parts
              let seg = getLineSegmentInBox(c.a, c.b, c.c, minX - w_plot*0.2, maxX + w_plot*0.2, minY - h_plot*0.2, maxY + h_plot*0.2);
              if (seg) {
                  let norm = Math.hypot(c.a, c.b);
                  if (norm > 0) {
                      let ux = c.a / norm;
                      let uy = c.b / norm;
                      let dx = c.sign === '<=' ? -ux : ux;
                      let dy = c.sign === '<=' ? -uy : uy;
                      
                      let sdx = dx;
                      let sdy = -dy;

                      let best_t = 0.5;
                      let best_score = -9999999;
                      
                      const arrowLenPx = 30;
                      const lblDistPx = 45;

                      // Sample candidate locations along the segment
                      for (let t = 0.1; t <= 0.9; t += 0.05) {
                          let qx = seg[0].x + t * (seg[1].x - seg[0].x);
                          let qy = seg[0].y + t * (seg[1].y - seg[0].y);
                          
                          let sx = this.screenX(qx);
                          let sy = this.screenY(qy);
                          
                          let lx = sx + sdx * lblDistPx;
                          let ly = sy + sdy * lblDistPx;
                          
                          let score = 0;
                          // Penalty for going too far from center of the visible segment
                          score -= 80 * Math.pow(t - 0.5, 2);

                          // Check canvas boundaries (keep labels inside screen)
                          if (lx - 15 < 10 || lx + 15 > this.width - 10 || ly - 10 < 10 || ly + 10 > this.height - 10) {
                              score -= 1000;
                          }

                          // Avoid overlapping canvas edges for base point
                          if (sx < 10 || sx > this.width - 10 || sy < 10 || sy > this.height - 10) {
                              score -= 200;
                          }

                          // Convert pixel distances to data units to check inside feasible region
                          let data_tip_x = qx + dx * (arrowLenPx / this.scale);
                          let data_tip_y = qy + dy * (arrowLenPx / this.scale);
                          let data_lbl_x = qx + dx * (lblDistPx / this.scale);
                          let data_lbl_y = qy + dy * (lblDistPx / this.scale);

                          let tipInside = isInsideFeasible(data_tip_x, data_tip_y);
                          let lblInside = isInsideFeasible(data_lbl_x, data_lbl_y);
                          let baseInside = isInsideFeasible(qx, qy);

                          if (tipInside) score -= 300;
                          if (lblInside) score -= 300;
                          if (!baseInside) score += 150;

                          // Check overlap with other collision boxes (already placed labels/vertices)
                          // Inflate candidate box slightly for padding (width 36px, height 24px)
                          let candidateBox = { x1: lx - 18, y1: ly - 12, x2: lx + 18, y2: ly + 12 };
                          let overlapCount = 0;
                          collisionBoxes.forEach(box => {
                              if (rectsOverlap(candidateBox, box)) {
                                  overlapCount++;
                              }
                          });
                          score -= overlapCount * 1000; // heavy penalty for overlapping

                          // Check distance to vertices (avoid cluttering vertex points)
                          if (this.data && this.data.vertices) {
                              this.data.vertices.forEach(v => {
                                  let vx = this.screenX(v.x1);
                                  let vy = this.screenY(v.x2);
                                  let d = Math.hypot(lx - vx, ly - vy);
                                  if (d < 45) {
                                      score -= 300 / (d / 10 + 0.1);
                                  }
                              });
                          }

                          if (score > best_score) {
                              best_score = score;
                              best_t = t;
                          }
                      }

                      let qx = seg[0].x + best_t * (seg[1].x - seg[0].x);
                      let qy = seg[0].y + best_t * (seg[1].y - seg[0].y);
                      
                      let sx = this.screenX(qx);
                      let sy = this.screenY(qy);
                      let lx = sx + sdx * lblDistPx;
                      let ly = sy + sdy * lblDistPx;
                      
                      // Add chosen label box to collisionBoxes
                      collisionBoxes.push({
                          x1: lx - 18,
                          y1: ly - 12,
                          x2: lx + 18,
                          y2: ly + 12
                      });

                      this.annotations.push({
                          type: 'constraint',
                          text: `(${c.index})`,
                          color: this.colors[idx % this.colors.length],
                          qx: qx, qy: qy,
                          dx: dx, dy: dy
                      });
                  }
              }
          });
      }

      // Objective function z
      if (this.data && (this.data.c1 !== 0 || this.data.c2 !== 0)) {
          let c1 = this.data.c1 || 0;
          let c2 = this.data.c2 || 0;
          let lcm = this.data.lcm_val || 0;
          let norm = Math.hypot(c1, c2);

          if (norm > 0) {
              let seg = getLineSegmentInBox(c1, c2, lcm, minX - w_plot*0.2, maxX + w_plot*0.2, minY - h_plot*0.2, maxY + h_plot*0.2);
              if (seg) {
                  let ux = c1 / norm;
                  let uy = c2 / norm;
                  let dx = this.data.is_max ? ux : -ux;
                  let dy = this.data.is_max ? uy : -uy;
                  
                  let sdx = dx;
                  let sdy = -dy;

                  let best_t = 0.5;
                  let best_score = -9999999;
                  
                  const arrowLenPx = 35;
                  const lblDistPx = 50;

                  for (let t = 0.1; t <= 0.9; t += 0.05) {
                      let qx = seg[0].x + t * (seg[1].x - seg[0].x);
                      let qy = seg[0].y + t * (seg[1].y - seg[0].y);
                      
                      let sx = this.screenX(qx);
                      let sy = this.screenY(qy);
                      let lx = sx + sdx * lblDistPx;
                      let ly = sy + sdy * lblDistPx;
                      
                      let score = 0;
                      score -= 80 * Math.pow(t - 0.5, 2);

                      if (lx - 15 < 10 || lx + 15 > this.width - 10 || ly - 15 < 10 || ly + 15 > this.height - 10) {
                          score -= 1000;
                      }

                      if (sx < 10 || sx > this.width - 10 || sy < 10 || sy > this.height - 10) {
                          score -= 200;
                      }

                      let data_tip_x = qx + dx * (arrowLenPx / this.scale);
                      let data_tip_y = qy + dy * (arrowLenPx / this.scale);
                      let data_lbl_x = qx + dx * (lblDistPx / this.scale);
                      let data_lbl_y = qy + dy * (lblDistPx / this.scale);

                      let tipInside = isInsideFeasible(data_tip_x, data_tip_y);
                      let lblInside = isInsideFeasible(data_lbl_x, data_lbl_y);
                      let baseInside = isInsideFeasible(qx, qy);

                      if (tipInside) score -= 300;
                      if (lblInside) score -= 300;
                      if (!baseInside) score += 150;

                      let candidateBox = { x1: lx - 15, y1: ly - 15, x2: lx + 15, y2: ly + 15 };
                      let overlapCount = 0;
                      collisionBoxes.forEach(box => {
                          if (rectsOverlap(candidateBox, box)) {
                              overlapCount++;
                          }
                      });
                      score -= overlapCount * 1000;

                      if (this.data && this.data.vertices) {
                          this.data.vertices.forEach(v => {
                              let vx = this.screenX(v.x1);
                              let vy = this.screenY(v.x2);
                              let d = Math.hypot(lx - vx, ly - vy);
                              if (d < 45) {
                                  score -= 300 / (d / 10 + 0.1);
                              }
                          });
                      }

                      if (score > best_score) {
                          best_score = score;
                          best_t = t;
                      }
                  }

                  let qx = seg[0].x + best_t * (seg[1].x - seg[0].x);
                  let qy = seg[0].y + best_t * (seg[1].y - seg[0].y);

                  this.annotations.push({
                      type: 'objective',
                      text: "z",
                      color: '#d62728',
                      qx: qx, qy: qy,
                      dx: dx, dy: dy
                  });
              }
          }
      }
  }
  
  setupEvents() {
    window.addEventListener('resize', () => {
      this.resizeCanvas();
    });
    
    // Xử lý kéo thả (Pan)
    this.canvas.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.lastMouseX = e.clientX;
      this.lastMouseY = e.clientY;
      this.canvas.style.cursor = 'grabbing';
    });
    
    window.addEventListener('mouseup', () => {
      this.isDragging = false;
      this.canvas.style.cursor = 'grab';
    });
    
    window.addEventListener('mousemove', (e) => {
      if (!this.isDragging) return;
      const dx = e.clientX - this.lastMouseX;
      const dy = e.clientY - this.lastMouseY;
      this.offsetX += dx;
      this.offsetY += dy;
      this.lastMouseX = e.clientX;
      this.lastMouseY = e.clientY;
      this.needsRedraw = true;
    });
    
    // Xử lý cuộn chuột (Zoom)
    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      
      const rect = this.canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      
      // Tọa độ data tại điểm trỏ chuột
      const dataX = (mouseX - this.offsetX) / this.scale;
      const dataY = -(mouseY - this.offsetY) / this.scale;
      
      // Tính toán scale mới
      const zoomFactor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
      
      // Giới hạn zoom để không bị lỗi
      if (this.scale * zoomFactor < 5 || this.scale * zoomFactor > 2000) return;
      
      this.scale *= zoomFactor;
      
      // Cập nhật lại offset để giữ nguyên điểm trỏ chuột
      this.offsetX = mouseX - dataX * this.scale;
      this.offsetY = mouseY - (-dataY * this.scale);
      
      this.needsRedraw = true;
    }, { passive: false });
    
    // Hỗ trợ cảm ứng (Touch devices)
    let lastTouchDistance = 0;
    this.canvas.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        this.isDragging = true;
        this.lastMouseX = e.touches[0].clientX;
        this.lastMouseY = e.touches[0].clientY;
      } else if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        lastTouchDistance = Math.hypot(dx, dy);
      }
    }, {passive: false});
    
    this.canvas.addEventListener('touchmove', (e) => {
      e.preventDefault();
      if (e.touches.length === 1 && this.isDragging) {
        const dx = e.touches[0].clientX - this.lastMouseX;
        const dy = e.touches[0].clientY - this.lastMouseY;
        this.offsetX += dx;
        this.offsetY += dy;
        this.lastMouseX = e.touches[0].clientX;
        this.lastMouseY = e.touches[0].clientY;
        this.needsRedraw = true;
      } else if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const dist = Math.hypot(dx, dy);
        
        if (lastTouchDistance > 0) {
          const zoomFactor = dist / lastTouchDistance;
          if (this.scale * zoomFactor >= 5 && this.scale * zoomFactor <= 2000) {
              const centerX = (e.touches[0].clientX + e.touches[1].clientX) / 2;
              const centerY = (e.touches[0].clientY + e.touches[1].clientY) / 2;
              const rect = this.canvas.getBoundingClientRect();
              const mouseX = centerX - rect.left;
              const mouseY = centerY - rect.top;
              
              const dataX = (mouseX - this.offsetX) / this.scale;
              const dataY = -(mouseY - this.offsetY) / this.scale;
              
              this.scale *= zoomFactor;
              this.offsetX = mouseX - dataX * this.scale;
              this.offsetY = mouseY - (-dataY * this.scale);
              this.needsRedraw = true;
          }
        }
        lastTouchDistance = dist;
      }
    }, {passive: false});
    
    this.canvas.addEventListener('touchend', () => {
      this.isDragging = false;
      lastTouchDistance = 0;
    });
  }
  
  // Các hàm chuyển đổi tọa độ
  screenX(dataX) { return this.offsetX + dataX * this.scale; }
  screenY(dataY) { return this.offsetY - dataY * this.scale; }
  dataX(screenX) { return (screenX - this.offsetX) / this.scale; }
  dataY(screenY) { return -(screenY - this.offsetY) / this.scale; }
  
  renderLoop() {
    if (this.needsRedraw) {
      this.draw();
      this.needsRedraw = false;
    }
    requestAnimationFrame(() => this.renderLoop());
  }
  
  draw() {
    this.computeAnnotations();
    
    // Xóa canvas
    this.ctx.clearRect(0, 0, this.width, this.height);
    this.ctx.fillStyle = '#ffffff';
    this.ctx.fillRect(0, 0, this.width, this.height);
    
    this.drawGrid();
    this.drawFeasibleRegion();
    this.drawAxes();
    this.drawConstraints();
    this.drawObjectiveFunction();
    this.drawVertices();
  }
  
  drawGrid() {
    this.ctx.strokeStyle = '#f0f0f0';
    this.ctx.lineWidth = 1;
    this.ctx.beginPath();
    
    // Tính toán step lưới thông minh
    // Muốn khoảng cách lưới khoảng 50 - 150 pixels
    const minGridPix = 50;
    let step = 1;
    let power = Math.pow(10, Math.floor(Math.log10(minGridPix / this.scale)));
    
    if ((power * this.scale) < minGridPix) {
      if ((power * 2 * this.scale) >= minGridPix) step = power * 2;
      else if ((power * 5 * this.scale) >= minGridPix) step = power * 5;
      else step = power * 10;
    } else {
      step = power;
    }
    
    const minX = this.dataX(0);
    const maxX = this.dataX(this.width);
    const minY = this.dataY(this.height);
    const maxY = this.dataY(0);
    
    // Lưới dọc
    let startX = Math.floor(minX / step) * step;
    for (let x = startX; x <= maxX; x += step) {
      const sx = this.screenX(x);
      this.ctx.moveTo(sx, 0);
      this.ctx.lineTo(sx, this.height);
    }
    
    // Lưới ngang
    let startY = Math.floor(minY / step) * step;
    for (let y = startY; y <= maxY; y += step) {
      const sy = this.screenY(y);
      this.ctx.moveTo(0, sy);
      this.ctx.lineTo(this.width, sy);
    }
    
    this.ctx.stroke();
  }
  
  drawAxes() {
    this.ctx.strokeStyle = '#000000';
    this.ctx.lineWidth = 1.5;
    this.ctx.beginPath();
    
    // Trục X
    const y0 = this.screenY(0);
    if (y0 >= 0 && y0 <= this.height) {
      this.ctx.moveTo(0, y0);
      this.ctx.lineTo(this.width, y0);
    }
    
    // Trục Y
    const x0 = this.screenX(0);
    if (x0 >= 0 && x0 <= this.width) {
      this.ctx.moveTo(x0, 0);
      this.ctx.lineTo(x0, this.height);
    }
    
    this.ctx.stroke();
    
    // Tính step tương tự grid
    const minGridPix = 50;
    let step = 1;
    let power = Math.pow(10, Math.floor(Math.log10(minGridPix / this.scale)));
    if ((power * this.scale) < minGridPix) {
      if ((power * 2 * this.scale) >= minGridPix) step = power * 2;
      else if ((power * 5 * this.scale) >= minGridPix) step = power * 5;
      else step = power * 10;
    } else {
      step = power;
    }

    const minX = this.dataX(0);
    const maxX = this.dataX(this.width);
    const minY = this.dataY(this.height);
    const maxY = this.dataY(0);

    const formatLabel = (val) => {
        if (Math.abs(val) < 1e-10) return "0";
        let str = val.toPrecision(10);
        return parseFloat(str).toString(); // remove trailing zeros
    };

    this.ctx.fillStyle = '#000000';
    this.ctx.font = '12px sans-serif';

    // Vị trí trục X gắn nhãn (sticky)
    let drawY0 = y0;
    if (drawY0 > this.height - 15) drawY0 = this.height - 15;
    if (drawY0 < 5) drawY0 = 5;

    // Trục X nhãn
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'top';
    let startX = Math.floor(minX / step) * step;
    for (let x = startX; x <= maxX; x += step) {
      if (Math.abs(x) < 1e-10) continue;
      const sx = this.screenX(x);
      
      // Vẽ vạch nhỏ trên trục nếu trục đang hiển thị
      if (y0 >= 0 && y0 <= this.height) {
          this.ctx.beginPath();
          this.ctx.moveTo(sx, y0 - 3);
          this.ctx.lineTo(sx, y0 + 3);
          this.ctx.stroke();
      }
      
      this.ctx.fillText(formatLabel(x), sx, drawY0 + 6);
    }

    // Vị trí trục Y gắn nhãn (sticky)
    let drawX0 = x0;
    if (drawX0 > this.width - 25) drawX0 = this.width - 25;
    if (drawX0 < 25) drawX0 = 25;

    // Trục Y nhãn
    this.ctx.textAlign = 'right';
    this.ctx.textBaseline = 'middle';
    let startY = Math.floor(minY / step) * step;
    for (let y = startY; y <= maxY; y += step) {
      if (Math.abs(y) < 1e-10) continue;
      const sy = this.screenY(y);
      
      // Vẽ vạch nhỏ
      if (x0 >= 0 && x0 <= this.width) {
          this.ctx.beginPath();
          this.ctx.moveTo(x0 - 3, sy);
          this.ctx.lineTo(x0 + 3, sy);
          this.ctx.stroke();
      }
      
      this.ctx.fillText(formatLabel(y), drawX0 - 6, sy);
    }

    // Góc tọa độ 0
    this.ctx.textAlign = 'right';
    this.ctx.textBaseline = 'top';
    this.ctx.fillText("0", drawX0 - 4, drawY0 + 4);
  }
  
  drawFeasibleRegion() {
    if (!this.data || this.data.res === "Infeasible" || !this.data.constraints) return;
    
    const ctx = this.ctx;
    ctx.save();
    
    // Mở một vùng clipping cực lớn
    ctx.beginPath();
    // Vùng vẽ mặc định rộng hơn canvas một chút
    const cx = this.width / 2;
    const cy = this.height / 2;
    const R = Math.max(this.width, this.height) * 10; 
    
    // Định nghĩa khung vuông bao quanh rất lớn
    const minX = this.dataX(-R);
    const maxX = this.dataX(this.width + R);
    const minY = this.dataY(this.height + R);
    const maxY = this.dataY(-R);
    
    // Mảng các đa giác, ban đầu là 1 hình vuông rất lớn
    let polygon = [
        {x: minX, y: minY},
        {x: maxX, y: minY},
        {x: maxX, y: maxY},
        {x: minX, y: maxY}
    ];
    
    // Cắt đa giác bằng từng nửa mặt phẳng
    const clipPolygon = (poly, a, b, c, sign) => {
        if (!poly || poly.length === 0) return [];
        const out = [];
        const evalPt = (p) => {
            const v = a * p.x + b * p.y - c;
            if (sign === '<=') return v <= 1e-6;
            if (sign === '>=') return v >= -1e-6;
            if (sign === '=') return Math.abs(v) <= 1e-6; // Không vẽ miền cho = 
            return true;
        };
        
        for (let i = 0; i < poly.length; i++) {
            const p1 = poly[i];
            const p2 = poly[(i + 1) % poly.length];
            
            const p1Inside = evalPt(p1);
            const p2Inside = evalPt(p2);
            
            if (p1Inside) out.push(p1);
            
            if (p1Inside !== p2Inside) {
                // Tính giao điểm
                const val1 = a * p1.x + b * p1.y - c;
                const val2 = a * p2.x + b * p2.y - c;
                const t = val1 / (val1 - val2);
                out.push({
                    x: p1.x + t * (p2.x - p1.x),
                    y: p1.y + t * (p2.y - p1.y)
                });
            }
        }
        return out;
    };
    
    // Áp dụng các ràng buộc
    this.data.constraints.forEach(c => {
        // Bỏ qua nếu là =, không tạo ra diện tích
        if (c.sign === '=') return;
        polygon = clipPolygon(polygon, c.a, c.b, c.c, c.sign);
    });
    
    // Áp dụng ràng buộc dấu
    if (this.data.signs.x1 === 'pos') polygon = clipPolygon(polygon, -1, 0, 0, '<='); // -x1 <= 0 -> x1 >= 0
    if (this.data.signs.x1 === 'neg') polygon = clipPolygon(polygon, 1, 0, 0, '<=');
    if (this.data.signs.x2 === 'pos') polygon = clipPolygon(polygon, 0, -1, 0, '<=');
    if (this.data.signs.x2 === 'neg') polygon = clipPolygon(polygon, 0, 1, 0, '<=');
    
    if (polygon.length > 2) {
        ctx.beginPath();
        ctx.moveTo(this.screenX(polygon[0].x), this.screenY(polygon[0].y));
        for (let i = 1; i < polygon.length; i++) {
            ctx.lineTo(this.screenX(polygon[i].x), this.screenY(polygon[i].y));
        }
        ctx.closePath();
        ctx.fillStyle = 'rgba(135, 206, 250, 0.4)'; // #87CEFA
        ctx.fill();
    }
    
    ctx.restore();
  }
  
  drawConstraints() {
    if (!this.data || !this.data.constraints) return;
    
    const minXData = this.dataX(0);
    const maxXData = this.dataX(this.width);
    const minYData = this.dataY(this.height);
    const maxYData = this.dataY(0);
    
    this.data.constraints.forEach((c, idx) => {
        const color = this.colors[idx % this.colors.length];
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2.5;
        this.ctx.beginPath();
        
        let pts = [];
        // Cắt với 4 biên của khung nhìn hiện tại (mở rộng thêm tí)
        const ext = 10; // units
        const L = minXData - ext, R = maxXData + ext, B = minYData - ext, T = maxYData + ext;
        
        if (Math.abs(c.b) > 1e-7) {
            pts.push({x: L, y: (c.c - c.a * L) / c.b});
            pts.push({x: R, y: (c.c - c.a * R) / c.b});
        }
        if (Math.abs(c.a) > 1e-7) {
            pts.push({x: (c.c - c.b * B) / c.a, y: B});
            pts.push({x: (c.c - c.b * T) / c.a, y: T});
        }
        
        // Lọc các điểm nằm trong khung mở rộng
        let validPts = pts.filter(p => p.x >= L-1 && p.x <= R+1 && p.y >= B-1 && p.y <= T+1);
        
        if (validPts.length >= 2) {
            this.ctx.moveTo(this.screenX(validPts[0].x), this.screenY(validPts[0].y));
            this.ctx.lineTo(this.screenX(validPts[1].x), this.screenY(validPts[1].y));
            this.ctx.stroke();
        }
    });

    if (this.annotations) {
        this.annotations.forEach(ann => {
            if (ann.type !== 'constraint') return;
            
            const sx = this.screenX(ann.qx);
            const sy = this.screenY(ann.qy);
            
            const arrowLenPx = 30;
            const ex = sx + ann.dx * arrowLenPx;
            const ey = sy - ann.dy * arrowLenPx; // -dy because screen Y is inverted
            
            // Vẽ cán mũi tên
            this.ctx.strokeStyle = ann.color;
            this.ctx.lineWidth = 2.5;
            this.ctx.beginPath();
            this.ctx.moveTo(sx, sy);
            this.ctx.lineTo(ex, ey);
            this.ctx.stroke();

            // Vẽ đầu mũi tên dạng tam giác đặc
            const headlen = 10;
            const angle = Math.atan2(-ann.dy, ann.dx);
            this.ctx.beginPath();
            this.ctx.moveTo(ex, ey);
            this.ctx.lineTo(ex - headlen * Math.cos(angle - Math.PI / 6), ey - headlen * Math.sin(angle - Math.PI / 6));
            this.ctx.lineTo(ex - headlen * Math.cos(angle + Math.PI / 6), ey - headlen * Math.sin(angle + Math.PI / 6));
            this.ctx.closePath();
            this.ctx.fillStyle = ann.color;
            this.ctx.fill();

            // Vẽ text
            const tx = sx + ann.dx * (arrowLenPx + 15);
            const ty = sy - ann.dy * (arrowLenPx + 15);

            this.ctx.fillStyle = ann.color;
            this.ctx.font = 'bold 13px sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.shadowColor = "white";
            this.ctx.shadowBlur = 4;
            this.ctx.fillText(ann.text, tx, ty);
            this.ctx.shadowBlur = 0;
        });
    }
  }
  
  drawObjectiveFunction() {
    if (!this.data || (this.data.c1 === 0 && this.data.c2 === 0)) return;
    
    const c1 = this.data.c1;
    const c2 = this.data.c2;
    const val = this.data.lcm_val || 0;
    
    this.ctx.strokeStyle = '#d62728'; // red
    this.ctx.lineWidth = 2.5;
    
    // Vẽ z dashed line
    this.ctx.setLineDash([5, 5]);
    this.ctx.beginPath();
    
    const minXData = this.dataX(0);
    const maxXData = this.dataX(this.width);
    const minYData = this.dataY(this.height);
    const maxYData = this.dataY(0);
    const ext = 10;
    const L = minXData - ext, R = maxXData + ext, B = minYData - ext, T = maxYData + ext;
    
    let pts = [];
    if (Math.abs(c2) > 1e-7) {
        pts.push({x: L, y: (val - c1 * L) / c2});
        pts.push({x: R, y: (val - c1 * R) / c2});
    }
    if (Math.abs(c1) > 1e-7) {
        pts.push({x: (val - c2 * B) / c1, y: B});
        pts.push({x: (val - c2 * T) / c1, y: T});
    }
    
    let validPts = pts.filter(p => p.x >= L-1 && p.x <= R+1 && p.y >= B-1 && p.y <= T+1);
    if (validPts.length >= 2) {
        this.ctx.moveTo(this.screenX(validPts[0].x), this.screenY(validPts[0].y));
        this.ctx.lineTo(this.screenX(validPts[1].x), this.screenY(validPts[1].y));
        this.ctx.stroke();
    }
    
    const norm = Math.hypot(c1, c2);
    
    // Vẽ hai đường +- vô cùng
    if (norm > 0) {
        // Cố định khoảng cách 2 đường +- vô cùng rộng ra (280 pixels) trên màn hình
        const offsetVal = (280 / this.scale) * norm;
        
        let dx = this.data.is_max ? c1/norm : -c1/norm;
        let dy = this.data.is_max ? c2/norm : -c2/norm;
        
        const drawParallelLine = (lcm_val) => {
            let pts_inf = [];
            if (Math.abs(c2) > 1e-7) {
                pts_inf.push({x: L, y: (lcm_val - c1 * L) / c2});
                pts_inf.push({x: R, y: (lcm_val - c1 * R) / c2});
            }
            if (Math.abs(c1) > 1e-7) {
                pts_inf.push({x: (lcm_val - c2 * B) / c1, y: B});
                pts_inf.push({x: (lcm_val - c2 * T) / c1, y: T});
            }
            let valid = pts_inf.filter(p => p.x >= L-1 && p.x <= R+1 && p.y >= B-1 && p.y <= T+1);
            if (valid.length >= 2) {
                this.ctx.strokeStyle = 'rgba(214, 39, 40, 0.4)'; // r: 0.4 alpha
                this.ctx.beginPath();
                this.ctx.moveTo(this.screenX(valid[0].x), this.screenY(valid[0].y));
                this.ctx.lineTo(this.screenX(valid[1].x), this.screenY(valid[1].y));
                this.ctx.stroke();
                
                // Mũi tên nhỏ ở giữa đoạn trên màn hình
                const mx = (valid[0].x + valid[1].x) / 2;
                const my = (valid[0].y + valid[1].y) / 2;
                const sx = this.screenX(mx);
                const sy = this.screenY(my);
                const ex = sx + dx * 20;
                const ey = sy - dy * 20;
                
                this.ctx.beginPath();
                this.ctx.moveTo(sx, sy);
                this.ctx.lineTo(ex, ey);
                this.ctx.stroke();
                
                const angle = Math.atan2(-dy, dx);
                this.ctx.beginPath();
                this.ctx.moveTo(ex, ey);
                this.ctx.lineTo(ex - 6 * Math.cos(angle - Math.PI / 6), ey - 6 * Math.sin(angle - Math.PI / 6));
                this.ctx.lineTo(ex - 6 * Math.cos(angle + Math.PI / 6), ey - 6 * Math.sin(angle + Math.PI / 6));
                this.ctx.closePath();
                this.ctx.fillStyle = 'rgba(214, 39, 40, 0.4)';
                this.ctx.fill();
            }
        };
        
        drawParallelLine(val + offsetVal);
        drawParallelLine(val - offsetVal);
    }
    
    this.ctx.setLineDash([]); // Reset
    
    // Vẽ mũi tên và nhãn z cố định ở tọa độ data đã tối ưu hóa
    if (this.annotations) {
        let ann = this.annotations.find(a => a.type === 'objective');
        if (ann) {
            const sx = this.screenX(ann.qx);
            const sy = this.screenY(ann.qy);
            
            const arrowLenPx = 35;
            const ex = sx + ann.dx * arrowLenPx;
            const ey = sy - ann.dy * arrowLenPx;
            
            this.ctx.strokeStyle = ann.color;
            this.ctx.lineWidth = 2.5;
            this.ctx.beginPath();
            this.ctx.moveTo(sx, sy);
            this.ctx.lineTo(ex, ey);
            this.ctx.stroke();

            const headlen = 12;
            const angle = Math.atan2(-ann.dy, ann.dx);
            this.ctx.beginPath();
            this.ctx.moveTo(ex, ey);
            this.ctx.lineTo(ex - headlen * Math.cos(angle - Math.PI / 6), ey - headlen * Math.sin(angle - Math.PI / 6));
            this.ctx.lineTo(ex - headlen * Math.cos(angle + Math.PI / 6), ey - headlen * Math.sin(angle + Math.PI / 6));
            this.ctx.closePath();
            this.ctx.fillStyle = ann.color;
            this.ctx.fill();

            const tx = sx + ann.dx * (arrowLenPx + 15);
            const ty = sy - ann.dy * (arrowLenPx + 15);

            this.ctx.fillStyle = ann.color;
            this.ctx.font = 'bold 14px sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.shadowColor = "white";
            this.ctx.shadowBlur = 4;
            this.ctx.fillText(ann.text, tx, ty);
            this.ctx.shadowBlur = 0;
        }
    }
  }
  
  drawVertices() {
    if (!this.data || !this.data.vertices) return;
    
    this.ctx.fillStyle = 'red';
    this.ctx.font = 'bold 12px sans-serif';
    
    this.data.vertices.forEach(v => {
        const sx = this.screenX(v.x1);
        const sy = this.screenY(v.x2);
        
        // Chỉ vẽ nếu nằm trong màn hình
        if (sx >= -50 && sx <= this.width + 50 && sy >= -50 && sy <= this.height + 50) {
            // Vẽ điểm với viền trắng nổi bật
            this.ctx.beginPath();
            this.ctx.arc(sx, sy, 5, 0, Math.PI * 2);
            this.ctx.fillStyle = 'red';
            this.ctx.fill();
            this.ctx.strokeStyle = 'white';
            this.ctx.lineWidth = 1.5;
            this.ctx.stroke();
            
            const xStr = v.x1_str || (Number.isInteger(v.x1) ? v.x1 : v.x1.toFixed(2));
            const yStr = v.x2_str || (Number.isInteger(v.x2) ? v.x2 : v.x2.toFixed(2));
            
            // Vẽ nhãn (Bóng trắng cho dễ đọc)
            const text = `${v.name}(${xStr}, ${yStr})`;
            this.ctx.textAlign = 'left';
            this.ctx.textBaseline = 'bottom';
            
            this.ctx.shadowColor = "white";
            this.ctx.shadowBlur = 4;
            this.ctx.fillText(text, sx + 6, sy - 6);
            this.ctx.shadowBlur = 0; // Reset
        }
    });
  }
  
  // Hủy sự kiện khi bị thay thế
  destroy() {
      this.needsRedraw = false;
      // Trong ứng dụng thực tế có thể cần gỡ EventListener
  }
}

// Gắn vào window để gọi từ app.js
window.DesmosGraph = DesmosGraph;
