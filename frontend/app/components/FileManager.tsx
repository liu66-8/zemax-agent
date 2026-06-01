"use client";

import { useFileStore, useDesignStore, useProjectStore, type FileEntry, type RecentFile } from "@/app/stores";
import { useModal, ConfirmDialog } from "@/app/components/Modal";
import { FileText, FolderOpen, Upload, Download, Clock, HardDrive, Save } from "lucide-react";
import { useState } from "react";

export default function FileManager() {
  const { currentFile, recentFiles, workspaceFiles, setCurrentFile, addRecent, setWorkspaceFiles } = useFileStore();
  const { setLensData } = useDesignStore();
  const { current: project } = useProjectStore();
  const { open, close } = useModal();
  const [dragOver, setDragOver] = useState(false);

  const handleOpenFile = () => {
    const mockData = [
      { index: 1, surf_type: "Standard", radius: 0, thickness: 1e10, glass: "", semi_diameter: 25, conic: 0, is_stop: false },
      { index: 2, surf_type: "Standard", radius: 50, thickness: 5, glass: "N-BK7", semi_diameter: 25, conic: 0, is_stop: true },
      { index: 3, surf_type: "Standard", radius: -200, thickness: 50, glass: "", semi_diameter: 23, conic: 0, is_stop: false },
      { index: 4, surf_type: "Standard", radius: 0, thickness: 45, glass: "", semi_diameter: 10, conic: 0, is_stop: false },
    ];
    const name = "Cooke_Triplet_100mm.zmx";
    setLensData(mockData, 100, 4.0, 100);
    setCurrentFile(name);
    addRecent({ name, path: `workspace/${project?.id || "default"}/designs/${name}`, openedAt: new Date().toISOString() });
    close();
  };

  const openLoadDialog = () => open(
    <div>
      <h2>加载 ZMX 文件</h2>
      <div style={{
        border: "2px dashed var(--border)", borderRadius: 10, padding: "32px 24px", textAlign: "center",
        margin: "16px 0", background: dragOver ? "var(--accent-soft)" : "transparent",
        transition: "all 0.2s", cursor: "pointer",
      }}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleOpenFile(); }}>
        <Upload size={32} style={{ opacity: 0.3, marginBottom: 10 }} />
        <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>拖放 ZMX 文件到此处</p>
        <p style={{ fontSize: 11, color: "var(--text-tertiary)", marginTop: 4 }}>或点击按钮选择文件</p>
      </div>
      <div style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 11, color: "var(--text-tertiary)", marginBottom: 8 }}>最近打开的文件</p>
        {recentFiles.length === 0 ? (
          <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>暂无记录</p>
        ) : (
          recentFiles.slice(0, 5).map((f) => (
            <div key={f.path} className="card" style={{ marginBottom: 4, cursor: "pointer", fontSize: 12.5 }}
              onClick={handleOpenFile}>
              <FileText size={13} style={{ marginRight: 8, verticalAlign: -2 }} />
              {f.name}
              <span style={{ float: "right", color: "var(--text-tertiary)", fontSize: 10.5 }}>
                {new Date(f.openedAt).toLocaleDateString("zh-CN")}
              </span>
            </div>
          ))
        )}
      </div>
      <div className="modal-actions">
        <button className="btn btn-secondary" onClick={close}>取消</button>
        <button className="btn btn-primary" onClick={handleOpenFile}>
          <FolderOpen size={14} /> 浏览文件...
        </button>
      </div>
    </div>
  );

  const handleSave = () => open(
    <ConfirmDialog title="保存文件" message={`将当前设计保存为 ${currentFile || "新设计"}.zmx？`}
      onConfirm={close} onCancel={close} />
  );

  return (
    <div className="panel-box">
      <div className="panel-hdr">
        <FolderOpen size={14} style={{ color: "var(--warning)" }} />
        <h3>文件管理</h3>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          <button className="btn btn-secondary btn-sm" onClick={openLoadDialog}>
            <Upload size={12} /> 加载
          </button>
          <button className="btn btn-secondary btn-sm" onClick={handleSave}>
            <Save size={12} /> 保存
          </button>
        </div>
      </div>
      <div className="panel-body">
        {currentFile ? (
          <div>
            <div className="card" style={{ marginBottom: 10, borderColor: "var(--accent)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <FileText size={16} style={{ color: "var(--accent)" }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{currentFile}</div>
                  <div style={{ fontSize: 10.5, color: "var(--text-tertiary)", marginTop: 2 }}>
                    {project ? `项目: ${project.name}` : "未关联项目"}
                  </div>
                </div>
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6, marginBottom: 12 }}>
              <MiniCard icon={HardDrive} label="文件大小" value="12.4 KB" />
              <MiniCard icon={Clock} label="修改时间" value="今天 12:00" />
              <MiniCard icon={Download} label="关联分析" value="3 个" />
            </div>
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: "32px 0", color: "var(--text-tertiary)" }}>
            <FolderOpen size={36} style={{ opacity: 0.1, marginBottom: 10 }} />
            <p style={{ fontSize: 12.5 }}>未加载设计文件</p>
            <button className="btn btn-primary btn-sm" onClick={openLoadDialog} style={{ marginTop: 12 }}>
              打开 ZMX 文件
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function MiniCard({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div className="card" style={{ padding: "8px", textAlign: "center" }}>
      <Icon size={12} style={{ opacity: 0.4, marginBottom: 2 }} />
      <div style={{ fontSize: 10, color: "var(--text-tertiary)" }}>{label}</div>
      <div style={{ fontSize: 12, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
