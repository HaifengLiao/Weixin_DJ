const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// cookies保存目录
const COOKIES_DIR = path.join(__dirname, 'cookies');

// 从txt文件加载cookies
async function loadCookies(page, accountName) {
    try {
        const filePath = path.join(COOKIES_DIR, `${accountName}.txt`);
        const cookiesStr = fs.readFileSync(filePath, 'utf8');
        const cookies = JSON.parse(cookiesStr);
        await page.setCookie(...cookies);
        //console.log(`账号 ${accountName}: 成功加载Cookies`);
        return true;
    } catch (error) {
        console.log(`账号 ${accountName}: 未找到Cookies文件`);
        return false;
    }
}

// 配置启动Edge浏览器的函数
async function launchEdgeBrowser() {
    return await puppeteer.launch({
        headless: false,
        executablePath: process.platform === 'win32'
            ? 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
            : '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        defaultViewport: { width: 1280, height: 800 },
        args: [
            '--disable-web-security',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-features=IsolateOrigins,site-per-process',
            '--start-maximized',
            '--disable-blink-features=AutomationControlled',
            '--window-size=1200,1000', // 设置浏览器窗口大小
            '--window-position=700,10' // 设置浏览器窗口位置，x=100, y=10
        ],
        ignoreHTTPSErrors: true,
        timeout: 30000
    });
}

async function automateLogin(accountName, url, inputpassword) {
    const browser = await launchEdgeBrowser();
    const page = await browser.newPage();

    // 设置 Edge 的 User-Agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0');
    await page.setDefaultNavigationTimeout(30000);

    try {
        // 加载指定账号的cookies
        const hasCookies = await loadCookies(page, accountName);
        if (!hasCookies) {
            console.log(`账号 ${accountName}: 无法加载Cookies，退出。`);
            return;
        }

        await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });//没有网络请求在进行

        try {
            if (inputpassword!=='error'){// 检查是否存在访问密码的输入框
                const passwordInputSelector = 'input[name="pwd"]';
                const submitButtonSelector = 'button.visit_btn[type="submit"]'; // 提交按钮的选择器
                const passwordInput = await page.$(passwordInputSelector);// 检查是否存在输入框
                if (passwordInput) {
                    // 确保输入框可见
                    await page.waitForSelector(passwordInputSelector, { visible: true });
                    // 输入密码
                    const password = inputpassword; // 替换为实际的访问密码
                    await page.click(passwordInputSelector); // 点击输入框以激活
                    await page.type(passwordInputSelector, password, { delay: 100 });
                    const submitButton = await page.$(submitButtonSelector);// 检查提交按钮是否存在并点击
                    if (submitButton) {// 使用 Promise.all 确保 navigation 和 click 一起处理
                        await Promise.all([
                            page.waitForNavigation({ waitUntil: 'networkidle0' }),
                            page.click(submitButtonSelector) // 点击提交按钮
                        ]);
                        console.log('成功点击确认按钮，页面加载完成');
                    } else {console.log("提交按钮未找到");}
                } else {console.log("访问密码输入框未找到");}
            }
            // 检查是否存在"直接访问" 点击"直接访问"链接
            const directaccess = '#pcprompt-viewpc';
            const directaccessButton = await page.$(directaccess) !== null;
            if (directaccessButton) {
                await page.click('#pcprompt-viewpc', {
                    delay: Math.floor(Math.random() * 100) + 50
                });
                //console.log(`账号 ${accountName}: 已点击直接访问链接`);
                await new Promise(resolve => setTimeout(resolve, 1000));
            }else{console.log("不存在直接访问");}

            // 检查是否存在 商品界面的"一键领取" 按钮
            const oneClickSelector = '.btn-area .receBtn.animate-pulse';
            const oneClickButton = await page.$(oneClickSelector) !== null;
            if (oneClickButton) {
                // 获取提示框的文本内容
                const oneClickText = await page.evaluate(selector => {
                    const alertElement = document.querySelector(selector);
                    return alertElement ? alertElement.textContent.trim() : '';
                }, oneClickSelector);
                if (oneClickText === '一键领取'){
                    await page.click(oneClickSelector,{ delay: Math.floor(Math.random() * 100) + 50 });
                    //console.log(`账号 ${accountName}: 成功点击“一键领取”按钮`);

                    await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
                }else{
                    console.log(`账号 ${accountName}:弹窗：`,oneClickText);
                    await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
                }
            }

            // 检查是否存在 优惠卷界面的立即领取" 按钮
            const YHJlijilinqu = '.receive-btn-one.z-ind-1';
            const YHJlijilinquButton = await page.$(YHJlijilinqu) !== null;
            if (YHJlijilinquButton) {
                // 获取提示框的文本内容
                const YHJlijilinquText = await page.evaluate(selector => {
                    const alertElement = document.querySelector(selector);
                    return alertElement ? alertElement.textContent.trim() : '';
                }, YHJlijilinqu);
                if (YHJlijilinquText === '立即领取'){
                    await page.click(YHJlijilinqu,{ delay: Math.floor(Math.random() * 100) + 50 });
                    //console.log(`账号 ${accountName}: 成功点击“立即领取”按钮`);

                    await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
                }else{
                    console.log(`账号 ${accountName}:弹窗：`,YHJlijilinquText);
                    await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
                }
            }

            // 点击"立即领取"按钮
            const couponButtonsSelector = '.coupon-btns';
            const couponButtonsContainer = await page.$(couponButtonsSelector) !== null;
            if (couponButtonsContainer) {    
                // 获取提示框的文本内容
                const buttonText = await page.evaluate(selector => {
                    const alertElement = document.querySelector(selector);
                    return alertElement ? alertElement.textContent.trim() : '';
                }, couponButtonsSelector);

                // 根据不同的按钮文本进行处理
                if (buttonText === '立即领取') {
                    await page.click(couponButtonsSelector,{ delay: Math.floor(Math.random() * 100) + 50 });
                    await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
                    //console.log(`账号 ${accountName}: 已点击`);
                    // 检测检查提示框是否存在，并且打印提示
                    const loginAlertSelector = '.mod_alert_v2.show.fixed';
                    const loginAlertVisible = await page.$(loginAlertSelector) !== null;
                    if (loginAlertVisible) {
                        // 获取提示框的文本内容
                        const alertText = await page.evaluate(selector => {
                            const alertElement = document.querySelector(selector);
                            return alertElement ? alertElement.textContent.trim() : '';
                        }, loginAlertSelector);
                        console.log(`账号 ${accountName}:弹窗：`,alertText);
                    }else{
                        console.log(`账号 ${accountName}: 领取成功`);
                    }   

                } else if (buttonText === '已过期') {
                    console.log(`账号 ${accountName}: 已过期`);
                }
                else if (buttonText.includes('去活动页') || buttonText.includes('立即使用') || buttonText.includes('查看 “我的优惠券”')) 
                    {
                    console.log(`账号 ${accountName}: 已经领取过了`);
                } else {
                    throw new Error(`账号 ${accountName}:未找到"立即领取"按钮文本${buttonText}`);
                }
            }//else{console.log(`账号 ${accountName}: 普通立即领取`);}

        } catch (error) {
            throw error;
        }
    } catch (error) {
        console.error(error.message);
    } finally {
        await browser.close();
    }
}

// 读取账号文件并执行登录
(async () => {
    const accountNames = ['15977338187','17878136640','15019376950','13457645842','13471584355']; // 指定要使用的多个账号名称 15977338187
    const url = process.argv[2]; // 获取传入的URL参数
    const inputpassword = process.argv[3]; // 获取传入的密码参数
    
    if (!url) {
        console.error('未提供网址参数');
        return;
    }

    const loginPromises = accountNames.map(accountName => automateLogin(accountName, url, inputpassword));
    
    // 等待所有账号的登录任务完成
    await Promise.all(loginPromises);
})();
