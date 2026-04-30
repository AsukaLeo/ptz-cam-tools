#include "mainwindow.h"

#include <QApplication>
#include <QTabWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGridLayout>
#include <QLabel>
#include <QPushButton>
#include <QComboBox>
#include <QLineEdit>
#include <QSpinBox>
#include <QGroupBox>
#include <QFrame>
#include <QScrollArea>
#include <QListWidget>
#include <QStatusBar>
#include <QMessageBox>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
{
    setupUi();
    setWindowTitle("PTZ-Cam-Tools");
    resize(900, 720);
}

MainWindow::~MainWindow() = default;

void MainWindow::setupUi()
{
    auto *centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    auto *mainLayout = new QVBoxLayout(centralWidget);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    // Title bar
    createTitleBar();

    // Tab widget
    createTabWidget();

    // PTZ Panel (at bottom)
    createPtzPanel();

    // Status bar
    createStatusBar();
}

void MainWindow::createTitleBar()
{
    auto *titleBar = new QFrame(this);
    titleBar->setFixedHeight(40);
    titleBar->setStyleSheet("QFrame { background-color: #e8e8e8; border-bottom: 1px solid #ccc; }");

    auto *layout = new QHBoxLayout(titleBar);
    layout->setContentsMargins(12, 0, 12, 0);
    layout->setSpacing(8);

    // Title
    auto *titleLabel = new QLabel("PTZ-Cam-Tools", titleBar);
    titleLabel->setStyleSheet("font-size: 13px; color: #333; font-weight: normal;");
    layout->addWidget(titleLabel);

    layout->addStretch();

    // Window controls (min/max/close)
    auto createWinBtn = [&](const QString &text) {
        auto *btn = new QPushButton(text, titleBar);
        btn->setFixedSize(20, 20);
        btn->setStyleSheet(
            "QPushButton { background-color: #d0d0d0; border: 1px solid #aaa; "
            "border-radius: 3px; font-size: 10px; color: #333; }"
            "QPushButton:hover { background-color: #c0c0c0; }"
        );
        return btn;
    };

    layout->addWidget(createWinBtn("_"));
    layout->addWidget(createWinBtn("□"));
    layout->addWidget(createWinBtn("×"));

    centralWidget()->layout()->addWidget(titleBar);
}

void MainWindow::createTabWidget()
{
    m_tabWidget = new QTabWidget(this);
    m_tabWidget->setDocumentMode(true);
    m_tabWidget->setStyleSheet(
        "QTabWidget::pane { border: none; background-color: #fff; }"
        "QTabBar::tab { background-color: #e8e8e8; padding: 8px 16px; "
        "border: 1px solid transparent; border-bottom: none; "
        "border-radius: 4px 4px 0 0; color: #555; margin-bottom: -1px; }"
        "QTabBar::tab:hover { background-color: #ddd; }"
        "QTabBar::tab:selected { background-color: #fff; color: #0078d4; "
        "font-weight: 500; border-color: #ccc; }"
    );

    // Add tabs
    m_tabWidget->addTab(createUsbTab(), "USB预览");
    m_tabWidget->addTab(createRtspTab(), "RTSP");
    m_tabWidget->addTab(createNdiTab(), "NDI");
    m_tabWidget->addTab(createOnvifTab(), "ONVIF");
    m_tabWidget->addTab(createSettingsTab(), "设置");

    connect(m_tabWidget, &QTabWidget::currentChanged, this, &MainWindow::onTabChanged);

    centralWidget()->layout()->addWidget(m_tabWidget);
}

QWidget* MainWindow::createUsbTab()
{
    auto *page = new QWidget();
    auto *layout = new QVBoxLayout(page);
    layout->setContentsMargins(16, 16, 16, 16);
    layout->setSpacing(12);

    // Device selection row
    auto *deviceRow = new QHBoxLayout();
    deviceRow->setSpacing(8);

    auto *deviceLabel = new QLabel("设备:");
    deviceLabel->setFixedWidth(80);
    deviceLabel->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    deviceRow->addWidget(deviceLabel);

    auto *deviceCombo = new QComboBox();
    deviceCombo->setFixedWidth(200);
    deviceCombo->addItems({"USB Camera (1)", "USB Camera (2)"});
    deviceRow->addWidget(deviceCombo);

    auto *refreshBtn = new QPushButton("刷新");
    deviceRow->addWidget(refreshBtn);
    connect(refreshBtn, &QPushButton::clicked, this, &MainWindow::onUsbRefresh);

    auto *playBtn = new QPushButton("播放");
    playBtn->setStyleSheet(
        "QPushButton { background-color: #0078d4; color: #fff; border-color: #0066b8; "
        "padding: 5px 16px; border-radius: 3px; }"
        "QPushButton:hover { background-color: #0066b8; }"
    );
    deviceRow->addWidget(playBtn);
    connect(playBtn, &QPushButton::clicked, this, &MainWindow::onUsbPlay);

    deviceRow->addStretch();
    layout->addLayout(deviceRow);

    // Preview area
    auto *previewFrame = new QFrame();
    previewFrame->setFixedHeight(280);
    previewFrame->setStyleSheet(
        "QFrame { background-color: #1a1a1a; border: 2px solid #333; border-radius: 2px; }"
    );

    auto *previewLayout = new QVBoxLayout(previewFrame);
    previewLayout->setAlignment(Qt::AlignCenter);

    m_previewLabel = new QLabel("视频预览区");
    m_previewLabel->setStyleSheet("color: #666; font-size: 24px;");
    m_previewLabel->setAlignment(Qt::AlignCenter);
    previewLayout->addWidget(m_previewLabel);

    layout->addWidget(previewFrame);

    // Control strip
    auto *controlRow = new QHBoxLayout();
    controlRow->setSpacing(16);

    auto addControl = [&](const QString &label, const QStringList &items) {
        auto *hbox = new QHBoxLayout();
        hbox->setSpacing(8);
        auto *lbl = new QLabel(label);
        lbl->setFixedWidth(50);
        lbl->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
        hbox->addWidget(lbl);
        auto *combo = new QComboBox();
        combo->addItems(items);
        hbox->addWidget(combo);
        return hbox;
    };

    controlRow->addLayout(addControl("分辨率:", {"1920 x 1080", "1280 x 720", "640 x 480"}));
    controlRow->addLayout(addControl("格式:", {"YUY2", "MJPEG", "H264"}));
    controlRow->addLayout(addControl("帧率:", {"30 fps", "25 fps", "15 fps"}));
    controlRow->addStretch();

    layout->addLayout(controlRow);
    layout->addStretch();

    return page;
}

QWidget* MainWindow::createRtspTab()
{
    auto *page = new QWidget();
    auto *layout = new QVBoxLayout(page);
    layout->setContentsMargins(16, 16, 16, 16);
    layout->setSpacing(12);

    // URL row
    auto *urlRow = new QHBoxLayout();
    urlRow->setSpacing(8);

    auto *urlLabel = new QLabel("RTSP URL:");
    urlLabel->setFixedWidth(80);
    urlLabel->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    urlRow->addWidget(urlLabel);

    auto *urlEdit = new QLineEdit("rtsp://192.168.2.254/PSIA/Streaming/channels/h264");
    urlEdit->setFixedWidth(350);
    urlRow->addWidget(urlEdit);

    auto *connectBtn = new QPushButton("连接");
    connectBtn->setStyleSheet(
        "QPushButton { background-color: #0078d4; color: #fff; border-color: #0066b8; }"
        "QPushButton:hover { background-color: #0066b8; }"
    );
    urlRow->addWidget(connectBtn);
    connect(connectBtn, &QPushButton::clicked, this, &MainWindow::onRtspConnect);

    auto *disconnectBtn = new QPushButton("断开");
    disconnectBtn->setStyleSheet(
        "QPushButton { background-color: #c42b1c; color: #fff; border-color: #a52010; }"
        "QPushButton:hover { background-color: #a52010; }"
    );
    urlRow->addWidget(disconnectBtn);
    connect(disconnectBtn, &QPushButton::clicked, this, &MainWindow::onRtspDisconnect);

    urlRow->addStretch();
    layout->addLayout(urlRow);

    // Auth row
    auto *authRow = new QHBoxLayout();
    authRow->setSpacing(8);

    auto *userLabel = new QLabel("用户名:");
    userLabel->setFixedWidth(80);
    userLabel->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    authRow->addWidget(userLabel);

    auto *userEdit = new QLineEdit();
    userEdit->setPlaceholderText("admin");
    userEdit->setFixedWidth(120);
    authRow->addWidget(userEdit);

    auto *passLabel = new QLabel("密码:");
    passLabel->setFixedWidth(50);
    authRow->addWidget(passLabel);

    auto *passEdit = new QLineEdit();
    passEdit->setEchoMode(QLineEdit::Password);
    passEdit->setFixedWidth(120);
    authRow->addWidget(passEdit);

    authRow->addStretch();
    layout->addLayout(authRow);

    // Network row
    auto *netRow = new QHBoxLayout();
    netRow->setSpacing(8);

    auto *netLabel = new QLabel("网卡:");
    netLabel->setFixedWidth(80);
    netLabel->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    netRow->addWidget(netLabel);

    auto *netCombo = new QComboBox();
    netCombo->setFixedWidth(220);
    netCombo->addItems({"Realtek PCIe GbE - 192.168.1.100", "Intel Wi-Fi 6 - 192.168.1.101"});
    netRow->addWidget(netCombo);

    auto *protoCombo = new QComboBox();
    protoCombo->addItems({"UDP", "TCP"});
    netRow->addWidget(protoCombo);

    netRow->addStretch();
    layout->addLayout(netRow);

    // Preview area
    auto *previewFrame = new QFrame();
    previewFrame->setFixedHeight(280);
    previewFrame->setStyleSheet("QFrame { background-color: #1a1a1a; border: 2px solid #333; border-radius: 2px; }");

    auto *previewLayout = new QVBoxLayout(previewFrame);
    previewLayout->setAlignment(Qt::AlignCenter);
    auto *previewLabel = new QLabel("视频预览区");
    previewLabel->setStyleSheet("color: #666; font-size: 24px;");
    previewLabel->setAlignment(Qt::AlignCenter);
    previewLayout->addWidget(previewLabel);

    layout->addWidget(previewFrame);

    // Bitrate control
    auto *rateRow = new QHBoxLayout();
    auto *rateLabel = new QLabel("码率:");
    rateLabel->setFixedWidth(50);
    rateLabel->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    rateRow->addWidget(rateLabel);
    auto *rateCombo = new QComboBox();
    rateCombo->addItems({"自动", "4096 kbps", "2048 kbps"});
    rateRow->addWidget(rateCombo);
    rateRow->addStretch();
    layout->addLayout(rateRow);

    layout->addStretch();

    return page;
}

QWidget* MainWindow::createNdiTab()
{
    auto *page = new QWidget();
    auto *layout = new QVBoxLayout(page);
    layout->setContentsMargins(16, 16, 16, 16);
    layout->setSpacing(12);

    // Source row
    auto *srcRow = new QHBoxLayout();
    srcRow->setSpacing(8);

    auto *srcLabel = new QLabel("NDI 源:");
    srcLabel->setFixedWidth(80);
    srcLabel->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    srcRow->addWidget(srcLabel);

    auto *srcCombo = new QComboBox();
    srcCombo->setFixedWidth(200);
    srcCombo->addItem("(未发现 NDI 源)");
    srcRow->addWidget(srcCombo);

    auto *refreshBtn = new QPushButton("刷新");
    srcRow->addWidget(refreshBtn);
    connect(refreshBtn, &QPushButton::clicked, this, &MainWindow::onNdiRefresh);

    auto *connectBtn = new QPushButton("连接");
    connectBtn->setStyleSheet("QPushButton { background-color: #0078d4; color: #fff; border-color: #0066b8; }");
    srcRow->addWidget(connectBtn);
    connect(connectBtn, &QPushButton::clicked, this, &MainWindow::onNdiConnect);

    auto *disconnectBtn = new QPushButton("断开");
    disconnectBtn->setStyleSheet("QPushButton { background-color: #c42b1c; color: #fff; border-color: #a52010; }");
    srcRow->addWidget(disconnectBtn);
    connect(disconnectBtn, &QPushButton::clicked, this, &MainWindow::onNdiDisconnect);

    srcRow->addStretch();
    layout->addLayout(srcRow);

    // Preview
    auto *previewFrame = new QFrame();
    previewFrame->setFixedHeight(280);
    previewFrame->setStyleSheet("QFrame { background-color: #1a1a1a; border: 2px solid #333; border-radius: 2px; }");

    auto *previewLayout = new QVBoxLayout(previewFrame);
    previewLayout->setAlignment(Qt::AlignCenter);
    auto *previewLabel = new QLabel("视频预览区");
    previewLabel->setStyleSheet("color: #666; font-size: 24px;");
    previewLabel->setAlignment(Qt::AlignCenter);
    previewLayout->addWidget(previewLabel);

    layout->addWidget(previewFrame);
    layout->addStretch();

    return page;
}

QWidget* MainWindow::createOnvifTab()
{
    auto *page = new QWidget();
    auto *layout = new QVBoxLayout(page);
    layout->setContentsMargins(16, 16, 16, 16);
    layout->setSpacing(12);

    // IP row
    auto *ipRow = new QHBoxLayout();
    ipRow->setSpacing(8);

    auto *ipLabel = new QLabel("IP 地址:");
    ipLabel->setFixedWidth(80);
    ipLabel->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    ipRow->addWidget(ipLabel);

    auto *ipEdit = new QLineEdit("192.168.1.64");
    ipEdit->setFixedWidth(120);
    ipRow->addWidget(ipEdit);

    auto *portLabel = new QLabel("端口:");
    portLabel->setFixedWidth(40);
    ipRow->addWidget(portLabel);

    auto *portEdit = new QLineEdit("80");
    portEdit->setFixedWidth(60);
    ipRow->addWidget(portEdit);

    auto *discoverBtn = new QPushButton("发现");
    ipRow->addWidget(discoverBtn);
    connect(discoverBtn, &QPushButton::clicked, this, &MainWindow::onOnvifDiscover);

    auto *connectBtn = new QPushButton("连接");
    connectBtn->setStyleSheet("QPushButton { background-color: #0078d4; color: #fff; border-color: #0066b8; }");
    ipRow->addWidget(connectBtn);
    connect(connectBtn, &QPushButton::clicked, this, &MainWindow::onOnvifConnect);

    auto *disconnectBtn = new QPushButton("断开");
    disconnectBtn->setStyleSheet("QPushButton { background-color: #c42b1c; color: #fff; border-color: #a52010; }");
    ipRow->addWidget(disconnectBtn);
    connect(disconnectBtn, &QPushButton::clicked, this, &MainWindow::onOnvifDisconnect);

    ipRow->addStretch();
    layout->addLayout(ipRow);

    // Auth row
    auto *authRow = new QHBoxLayout();
    authRow->setSpacing(8);

    auto *userLabel = new QLabel("用户名:");
    userLabel->setFixedWidth(80);
    userLabel->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    authRow->addWidget(userLabel);

    auto *userEdit = new QLineEdit("admin");
    userEdit->setFixedWidth(100);
    authRow->addWidget(userEdit);

    auto *passLabel = new QLabel("密码:");
    passLabel->setFixedWidth(40);
    authRow->addWidget(passLabel);

    auto *passEdit = new QLineEdit();
    passEdit->setEchoMode(QLineEdit::Password);
    passEdit->setFixedWidth(100);
    authRow->addWidget(passEdit);

    authRow->addStretch();
    layout->addLayout(authRow);

    // Preview
    auto *previewFrame = new QFrame();
    previewFrame->setFixedHeight(280);
    previewFrame->setStyleSheet("QFrame { background-color: #1a1a1a; border: 2px solid #333; border-radius: 2px; }");

    auto *previewLayout = new QVBoxLayout(previewFrame);
    previewLayout->setAlignment(Qt::AlignCenter);
    auto *previewLabel = new QLabel("视频预览区");
    previewLabel->setStyleSheet("color: #666; font-size: 24px;");
    previewLabel->setAlignment(Qt::AlignCenter);
    previewLayout->addWidget(previewLabel);

    layout->addWidget(previewFrame);
    layout->addStretch();

    return page;
}

QWidget* MainWindow::createSettingsTab()
{
    auto *page = new QWidget();
    auto *layout = new QVBoxLayout(page);
    layout->setContentsMargins(16, 16, 16, 16);
    layout->setSpacing(20);

    // UI Settings section
    auto *uiSection = new QVBoxLayout();

    auto *uiTitle = new QLabel("界面设置");
    uiTitle->setStyleSheet("font-weight: 500; border-bottom: 1px solid #eee; padding-bottom: 4px;");
    uiSection->addWidget(uiTitle);

    auto *langRow = new QHBoxLayout();
    langRow->setSpacing(12);
    auto *langLabel = new QLabel("语言:");
    langLabel->setFixedWidth(100);
    auto *langCombo = new QComboBox();
    langCombo->addItems({"中文", "English"});
    langRow->addWidget(langLabel);
    langRow->addWidget(langCombo);
    langRow->addStretch();
    uiSection->addLayout(langRow);

    layout->addLayout(uiSection);

    // Network Settings section
    auto *netSection = new QVBoxLayout();

    auto *netTitle = new QLabel("网络设置");
    netTitle->setStyleSheet("font-weight: 500; border-bottom: 1px solid #eee; padding-bottom: 4px;");
    netSection->addWidget(netTitle);

    auto *netItemRow = new QHBoxLayout();
    netItemRow->setSpacing(12);

    auto *availLabel = new QLabel("可用网卡:");
    availLabel->setFixedWidth(100);
    netItemRow->addWidget(availLabel);

    auto *deviceList = new QListWidget();
    deviceList->setFixedHeight(80);
    deviceList->addItem("✓ Realtek PCIe GbE - 192.168.1.100");
    deviceList->addItem("  Intel Wi-Fi 6 - 192.168.1.101");
    deviceList->addItem("  VirtualBox Host-Only - 192.168.56.1");
    deviceList->setStyleSheet("QListWidget { border: 1px solid #aaa; border-radius: 3px; background: #fafafa; }");
    netItemRow->addWidget(deviceList, 1);

    netSection->addLayout(netItemRow);

    layout->addLayout(netSection);
    layout->addStretch();

    return page;
}

void MainWindow::createPtzPanel()
{
    auto *ptzPanel = new QFrame(this);
    ptzPanel->setStyleSheet(
        "QFrame { background-color: #f8f8f8; border: 1px solid #e0e0e0; border-radius: 4px; }"
    );

    auto *layout = new QVBoxLayout(ptzPanel);
    layout->setContentsMargins(12, 12, 12, 12);
    layout->setSpacing(8);

    // Title
    auto *titleLabel = new QLabel("PTZ 控制");
    titleLabel->setStyleSheet("font-size: 12px; font-weight: 500; color: #555;");
    layout->addWidget(titleLabel);

    // Controls container
    auto *controlsLayout = new QHBoxLayout();
    controlsLayout->setSpacing(16);
    controlsLayout->setAlignment(Qt::AlignLeft | Qt::AlignTop);

    // Directional pad (3x3 grid)
    auto *dpadLayout = new QGridLayout();
    dpadLayout->setSpacing(2);

    auto createPtzBtn = [&](const QString &text) {
        auto *btn = new QPushButton(text);
        btn->setFixedSize(32, 28);
        btn->setStyleSheet(
            "QPushButton { font-size: 12px; padding: 0; border: 1px solid #aaa; "
            "border-radius: 3px; background: #f5f5f5; }"
            "QPushButton:hover { background: #e5e5e5; }"
            "QPushButton:pressed { background: #d0d0d0; }"
        );
        return btn;
    };

    dpadLayout->addWidget(createPtzBtn("↖"), 0, 0);
    auto *upBtn = createPtzBtn("▲");
    dpadLayout->addWidget(upBtn, 0, 1);
    dpadLayout->addWidget(createPtzBtn("↗"), 0, 2);

    auto *leftBtn = createPtzBtn("◀");
    dpadLayout->addWidget(leftBtn, 1, 0);

    auto *stopBtn = createPtzBtn("●");
    stopBtn->setStyleSheet(
        "QPushButton { font-size: 10px; padding: 0; border: 1px solid #aaa; "
        "border-radius: 3px; background: #e0e0e0; color: #888; }"
    );
    dpadLayout->addWidget(stopBtn, 1, 1);

    auto *rightBtn = createPtzBtn("▶");
    dpadLayout->addWidget(rightBtn, 1, 2);

    dpadLayout->addWidget(createPtzBtn("↙"), 2, 0);
    auto *downBtn = createPtzBtn("▼");
    dpadLayout->addWidget(downBtn, 2, 1);
    dpadLayout->addWidget(createPtzBtn("↘"), 2, 2);

    connect(upBtn, &QPushButton::clicked, this, &MainWindow::onPtzUp);
    connect(downBtn, &QPushButton::clicked, this, &MainWindow::onPtzDown);
    connect(leftBtn, &QPushButton::clicked, this, &MainWindow::onPtzLeft);
    connect(rightBtn, &QPushButton::clicked, this, &MainWindow::onPtzRight);
    connect(stopBtn, &QPushButton::clicked, this, &MainWindow::onPtzStop);

    controlsLayout->addLayout(dpadLayout);

    // Zoom/Focus buttons
    auto *zoomLayout = new QVBoxLayout();
    zoomLayout->setSpacing(8);

    auto createCtrlBtn = [&](const QString &text) {
        auto *btn = new QPushButton(text);
        btn->setFixedWidth(60);
        btn->setStyleSheet("font-size: 11px; padding: 4px 8px;");
        return btn;
    };

    auto *zoomRow = new QHBoxLayout();
    zoomRow->setSpacing(8);
    auto *zoomInBtn = createCtrlBtn("Zoom+");
    auto *zoomOutBtn = createCtrlBtn("Zoom-");
    zoomRow->addWidget(zoomInBtn);
    zoomRow->addWidget(zoomOutBtn);
    zoomLayout->addLayout(zoomRow);

    auto *focusRow = new QHBoxLayout();
    focusRow->setSpacing(8);
    auto *focusInBtn = createCtrlBtn("Focus+");
    auto *focusOutBtn = createCtrlBtn("Focus-");
    focusRow->addWidget(focusInBtn);
    focusRow->addWidget(focusOutBtn);
    zoomLayout->addLayout(focusRow);

    connect(zoomInBtn, &QPushButton::clicked, this, &MainWindow::onZoomIn);
    connect(zoomOutBtn, &QPushButton::clicked, this, &MainWindow::onZoomOut);
    connect(focusInBtn, &QPushButton::clicked, this, &MainWindow::onFocusIn);
    connect(focusOutBtn, &QPushButton::clicked, this, &MainWindow::onFocusOut);

    controlsLayout->addLayout(zoomLayout);

    // Home/Stop buttons
    auto *homeLayout = new QVBoxLayout();
    homeLayout->setSpacing(8);

    auto *homeBtn = new QPushButton("Home");
    homeBtn->setFixedWidth(100);
    homeBtn->setStyleSheet("font-size: 11px; padding: 4px 16px;");
    homeLayout->addWidget(homeBtn);

    auto *stopBtn2 = new QPushButton("Stop");
    stopBtn2->setFixedWidth(100);
    stopBtn2->setStyleSheet("font-size: 11px; padding: 4px 16px;");
    homeLayout->addWidget(stopBtn2);

    connect(homeBtn, &QPushButton::clicked, this, &MainWindow::onPtzHome);
    connect(stopBtn2, &QPushButton::clicked, this, &MainWindow::onPtzStop);

    controlsLayout->addLayout(homeLayout);
    controlsLayout->addStretch();

    layout->addLayout(controlsLayout);

    // Add to main layout
    auto *mainLayout = qobject_cast<QVBoxLayout*>(centralWidget()->layout());
    if (mainLayout) {
        mainLayout->addWidget(ptzPanel);
    }
}

void MainWindow::createStatusBar()
{
    auto *statusBar = new QStatusBar(this);
    m_statusLabel = new QLabel("状态: 就绪");
    statusBar->addWidget(m_statusLabel);
    setStatusBar(statusBar);
}

// Slot implementations
void MainWindow::onTabChanged(int index)
{
    QString status;
    switch (index) {
        case 0: status = "状态: 就绪"; break;
        case 1: status = "状态: 未连接"; break;
        case 2: status = "状态: 未连接"; break;
        case 3: status = "状态: 未连接"; break;
        case 4: status = "状态: 设置"; break;
        default: status = "状态: 就绪";
    }
    if (m_statusLabel) {
        m_statusLabel->setText(status);
    }
}

void MainWindow::onUsbRefresh() { m_statusLabel->setText("状态: 刷新设备列表..."); }
void MainWindow::onUsbPlay() { m_statusLabel->setText("状态: 播放中"); }
void MainWindow::onRtspConnect() { m_statusLabel->setText("状态: 连接中..."); }
void MainWindow::onRtspDisconnect() { m_statusLabel->setText("状态: 已断开"); }
void MainWindow::onNdiRefresh() { m_statusLabel->setText("状态: 搜索 NDI 源..."); }
void MainWindow::onNdiConnect() { m_statusLabel->setText("状态: 连接中..."); }
void MainWindow::onNdiDisconnect() { m_statusLabel->setText("状态: 已断开"); }
void MainWindow::onOnvifDiscover() { m_statusLabel->setText("状态: 发现设备..."); }
void MainWindow::onOnvifConnect() { m_statusLabel->setText("状态: 连接中..."); }
void MainWindow::onOnvifDisconnect() { m_statusLabel->setText("状态: 已断开"); }

void MainWindow::onPtzLeftUp() { m_statusLabel->setText("状态: PTZ 左上"); }
void MainWindow::onPtzUp() { m_statusLabel->setText("状态: PTZ 上"); }
void MainWindow::onPtzRightUp() { m_statusLabel->setText("状态: PTZ 右上"); }
void MainWindow::onPtzLeft() { m_statusLabel->setText("状态: PTZ 左"); }
void MainWindow::onPtzStop() { m_statusLabel->setText("状态: PTZ 停止"); }
void MainWindow::onPtzRight() { m_statusLabel->setText("状态: PTZ 右"); }
void MainWindow::onPtzLeftDown() { m_statusLabel->setText("状态: PTZ 左下"); }
void MainWindow::onPtzDown() { m_statusLabel->setText("状态: PTZ 下"); }
void MainWindow::onPtzRightDown() { m_statusLabel->setText("状态: PTZ 右下"); }
void MainWindow::onPtzHome() { m_statusLabel->setText("状态: PTZ Home"); }
void MainWindow::onZoomIn() { m_statusLabel->setText("状态: Zoom +"); }
void MainWindow::onZoomOut() { m_statusLabel->setText("状态: Zoom -"); }
void MainWindow::onFocusIn() { m_statusLabel->setText("状态: Focus +"); }
void MainWindow::onFocusOut() { m_statusLabel->setText("状态: Focus -"); }
