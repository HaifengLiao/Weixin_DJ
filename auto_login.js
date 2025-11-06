const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// cookies保存目录（已是动态路径，保留）
const COOKIES_DIR = path.join(__dirname, 'cookies');
// 【关键修改】将固定路径改为动态路径：在当前脚本所在目录下创建screenshots文件夹
const CUSTOM_SCREENSHOT_DIR = path.join(__dirname, 'screenshots'); 

// 创建目录如果不存在（recursive: true 确保父目录不存在也能创建）
if (!fs.existsSync(CUSTOM_SCREENSHOT_DIR)) {
    fs.mkdirSync(CUSTOM_SCREENSHOT_DIR, { recursive: true });
    console.log(`已自动创建截图目录：${CUSTOM_SCREENSHOT_DIR}`); // 新增日志，方便确认路径
}

// 从txt文件加载cookies（无需修改）
async function loadCookies(page, accountName) {
    try {
        const filePath = path.join(COOKIES_DIR, `${accountName}.txt`);
        const cookiesStr = fs.readFileSync(filePath, 'utf8');
        const cookies = JSON.parse(cookiesStr);
        await page.setCookie(...cookies);
        return true;
    } catch (error) {
        console.log(`账号 ${accountName}: 未找到Cookies文件`);
        return false;
    }
}

// 配置启动Edge浏览器的函数（无需修改）
async function launchEdgeBrowser() {
    return await puppeteer.launch({
        headless: true,
        executablePath: process.platform === 'win32'
            ? 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
            : '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        defaultViewport: { width: 1280, height: 800 },
        args: [
            '--disable-web-security',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-blink-features=AutomationControlled',
            '--disable-gpu',
            '--disable-dev-shm-usage'
        ],
        ignoreHTTPSErrors: true,
        timeout: 30000
    });
}

async function automateLogin(accountName, url, inputpassword) {
    const browser = await launchEdgeBrowser();
    const page = await browser.newPage();

    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0');
    await page.setDefaultNavigationTimeout(30000);

    try {
        const hasCookies = await loadCookies(page, accountName);
        if (!hasCookies) {
            console.log(`账号 ${accountName}: 无法加载Cookies，退出。`);
            return;
        }

        await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });

        try {
            if (inputpassword!=='error'){
                const passwordInputSelector = 'input[name="pwd"]';
                const submitButtonSelector = 'button.visit_btn[type="submit"]';
                const passwordInput = await page.$(passwordInputSelector);
                if (passwordInput) {
                    await page.waitForSelector(passwordInputSelector, { visible: true });
                    const password = inputpassword;
                    await page.click(passwordInputSelector);
                    await page.type(passwordInputSelector, password, { delay: 100 });
                    const submitButton = await page.$(submitButtonSelector);
                    if (submitButton) {
                        await Promise.all([
                            page.waitForNavigation({ waitUntil: 'networkidle0' }),
                            page.click(submitButtonSelector)
                        ]);
                        console.log('成功点击确认按钮，页面加载完成');
                    } else {console.log("提交按钮未找到");}
                } else {console.log("访问密码输入框未找到");}
            }

            const directaccess = '#pcprompt-viewpc';
            const directaccessButton = await page.$(directaccess) !== null;
            if (directaccessButton) {
                await page.click('#pcprompt-viewpc', {
                    delay: Math.floor(Math.random() * 100) + 50
                });
                await new Promise(resolve => setTimeout(resolve, 1000));
            }else{console.log("不存在直接访问");}

            const oneClickSelector = '.btn-area .receBtn.animate-pulse';
            const oneClickButton = await page.$(oneClickSelector) !== null;
            if (oneClickButton) {
                const oneClickText = await page.evaluate(selector => {
                    const alertElement = document.querySelector(selector);
                    return alertElement ? alertElement.textContent.trim() : '';
                }, oneClickSelector);
                if (oneClickText === '一键领取'){
                    await page.click(oneClickSelector,{ delay: Math.floor(Math.random() * 100) + 50 });
                    console.log(`账号 ${accountName}: 成功点击"一键领取"按钮`);
                    await new Promise(resolve => setTimeout(resolve, 500));
                }else{
                    console.log(`账号 ${accountName}:弹窗：`,oneClickText);
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            }

            const YHJlijilinqu = '.receive-btn-one.z-ind-1';
            const YHJlijilinquButton = await page.$(YHJlijilinqu) !== null;
            if (YHJlijilinquButton) {
                const YHJlijilinquText = await page.evaluate(selector => {
                    const alertElement = document.querySelector(selector);
                    return alertElement ? alertElement.textContent.trim() : '';
                }, YHJlijilinqu);
                if (YHJlijilinquText === '立即领取'){
                    await page.click(YHJlijilinqu,{ delay: Math.floor(Math.random() * 100) + 50 });
                    console.log(`账号 ${accountName}: 成功点击"立即领取"按钮`);
                    await new Promise(resolve => setTimeout(resolve, 500));
                }else{
                    console.log(`账号 ${accountName}:弹窗：`,YHJlijilinquText);
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            }

            const couponButtonsSelector = '.coupon-btns';
            const couponButtonsContainer = await page.$(couponButtonsSelector) !== null;
            if (couponButtonsContainer) {    
                const buttonText = await page.evaluate(selector => {
                    const alertElement = document.querySelector(selector);
                    return alertElement ? alertElement.textContent.trim() : '';
                }, couponButtonsSelector);

                if (buttonText === '立即领取') {
                    await page.click(couponButtonsSelector,{ delay: Math.floor(Math.random() * 100) + 50 });
                    await new Promise(resolve => setTimeout(resolve, 500));
                    const loginAlertSelector = '.mod_alert_v2.show.fixed';
                    const loginAlertVisible = await page.$(loginAlertSelector) !== null;
                    if (loginAlertVisible) {
                        const alertText = await page.evaluate(selector => {
                            const alertElement = document.querySelector(selector);
                            return alertElement ? alertElement.textContent.trim() : '';
                        }, loginAlertSelector);
                        console.log(`${accountName}:`,alertText);
                    }else{
                        console.log(`账号 ${accountName}: 领取成功`);
                    }   

                } else if (buttonText === '已过期') {
                    console.log(`账号 ${accountName}: 已过期`);
                }
                else if (buttonText.includes('去活动页') || buttonText.includes('立即使用') || buttonText.includes('查看 "我的优惠券"')) 
                    {
                    console.log(`${accountName}: 已经领取过了`);
                } else {
                    throw new Error(`账号 ${accountName}:未找到"立即领取"按钮文本${buttonText}`);
                }
            }

            const couponSelector = '.dicount_coupon .coupon';
            const couponElements = await page.$$(couponSelector);
            if (couponElements.length > 0) {
                const couponsText = await page.evaluate(selector => {
                    const couponElements = document.querySelectorAll(selector);
                    return Array.from(couponElements).map(element => element.textContent.trim());
                }, couponSelector);

                couponsText.forEach(coupon => {
                    console.log(`发现优惠券：${coupon}`);
                });

                const specificCoupon = '满1200减240';
                if (couponsText.includes(specificCoupon)) {
                    console.log(`找到目标优惠券：${specificCoupon}`);
                    await page.click(couponSelector,{ delay: Math.floor(Math.random() * 100) + 50 });
                    await new Promise(resolve => setTimeout(resolve, 500));
                    console.log(`账号 ${accountName}: 已点击`);
                    await page.waitForSelector('#couponList');
                    const coupons = await page.$$('.coupon_voucher3');
                    for (const coupon of coupons) {
                        const description = await coupon.$eval('.coupon_voucher3_view_des', el => el.textContent.trim());
                        let buttonText;
                        try {
                            buttonText = await coupon.$eval('.coupon_voucher3_info_btn', el => el.textContent.trim());
                        } catch (error) {
                            console.log(`未找到领取按钮，可能该优惠券不可用：${description}`);
                            continue;
                        }
                        const isDisabled = await coupon.$eval('.coupon_voucher3_info_btn', el => el.classList.contains('disabled'));
                        if (!isDisabled) {
                            if (description.includes('满1200元可用') && buttonText === '领取') {
                                await coupon.$eval('.coupon_voucher3_info_btn', el => el.click());
                                await new Promise(resolve => setTimeout(resolve, 500));
                                console.log(`账号 ${accountName}: 已领取优惠券 - ${description}`);

                            } else if (description.includes('满2000元可用') && buttonText === '领取') {
                                await coupon.$eval('.coupon_voucher3_info_btn', el => el.click());
                                await new Promise(resolve => setTimeout(resolve, 500));
                                console.log(`账号 ${accountName}: 已领取优惠券 - ${description}`); 
                            } else {
                                console.log(`优惠券不可领取或已领取：${description}，按钮文本：${buttonText}`);
                            }
                        } else {
                            console.log(`优惠券不可领取：${description}，按钮文本：${buttonText}`);
                        }
                    }
                } else {
                    //console.log(`未找到目标优惠券：${specificCoupon}`);
                }
                await new Promise(resolve => setTimeout(resolve, 500));
            } else {
                //console.log("未找到任何优惠券信息");
            }

        } catch (error) {
            throw error;
        }
    } catch (error) {
        console.error(`账号 ${accountName}: ${error.message}`);
        // 错误截图路径已自动使用动态目录（无需修改）
        try {
            const errorScreenshotPath = path.join(CUSTOM_SCREENSHOT_DIR, `${accountName}_error.png`);
            await page.screenshot({ path: errorScreenshotPath });
            console.log(`错误截图已保存至：${errorScreenshotPath}`); // 新增日志，方便查找截图
        } catch (e) {
            // 忽略截图错误
        }
    } finally {
        await browser.close();
    }
}

// 读取账号文件并执行登录（无需修改）
(async () => {
    const accountNames = ['15977338187','15019376950','13457645842','13471584355','17878121881'];
    const url = process.argv[2];
    const inputpassword = process.argv[3];
    
    if (!url) {
        console.error('未提供网址参数');
        return;
    }

    const loginPromises = accountNames.map(accountName => automateLogin(accountName, url, inputpassword));
    await Promise.all(loginPromises);
})();
