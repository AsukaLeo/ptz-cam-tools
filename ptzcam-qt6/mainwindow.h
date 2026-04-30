#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QTabWidget>
#include <QMap>

QT_BEGIN_NAMESPACE
class QComboBox;
class QPushButton;
class QLabel;
class QLineEdit;
class QSpinBox;
class QWidget;
class QStackedWidget;
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void onTabChanged(int index);

    // USB Tab
    void onUsbRefresh();
    void onUsbPlay();

    // RTSP Tab
    void onRtspConnect();
    void onRtspDisconnect();

    // NDI Tab
    void onNdiRefresh();
    void onNdiConnect();
    void onNdiDisconnect();

    // ONVIF Tab
    void onOnvifDiscover();
    void onOnvifConnect();
    void onOnvifDisconnect();

    // PTZ Controls
    void onPtzLeftUp();
    void onPtzUp();
    void onPtzRightUp();
    void onPtzLeft();
    void onPtzStop();
    void onPtzRight();
    void onPtzLeftDown();
    void onPtzDown();
    void onPtzRightDown();
    void onPtzHome();
    void onZoomIn();
    void onZoomOut();
    void onFocusIn();
    void onFocusOut();

private:
    void setupUi();
    void createTitleBar();
    void createTabWidget();
    void createPtzPanel();
    void createStatusBar();

    // Tab pages
    QWidget* createUsbTab();
    QWidget* createRtspTab();
    QWidget* createNdiTab();
    QWidget* createOnvifTab();
    QWidget* createSettingsTab();

    QTabWidget *m_tabWidget;
    QLabel *m_statusLabel;
    QLabel *m_previewLabel;

    // Title bar widgets
    QPushButton *m_deviceBtn;
    QPushButton *m_settingsBtn;
};

#endif // MAINWINDOW_H
