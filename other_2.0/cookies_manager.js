const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// cookies保存目录
const COOKIES_DIR = path.join(__dirname, 'cookies');

// 确保cookies目录存在
if (!fs.existsSync(COOKIES_DIR)) {
    fs.mkdirSync(COOKIES_DIR);
}

// 保存cookies到txt文件
async function saveCookies(page, accountName) {
    const cookies = await page.cookies();
    const cookiesStr = JSON.stringify(cookies, null, 2);
    const filePath = path.join(COOKIES_DIR, `${accountName}.txt`);
    
    fs.writeFileSync(filePath, cookiesStr);
    console.log(`Cookies已保存到: ${filePath}`);
}

// 从txt文件加载cookies
async function loadCookies(page, accountName) {
    try {
        const filePath = path.join(COOKIES_DIR, `${accountName}.txt`);
        const cookiesStr = fs.readFileSync(filePath, 'utf8');
        const cookies = JSON.parse(cookiesStr);
        await page.setCookie(...cookies);
        console.log(`YES_账号 ${accountName} 的TK`);
        return true;
    } catch (error) {
        console.log(`未找到账号 ${accountName} 的TK`);
        return false;
    }
}

// 获取所有保存的账号列表
function getAccountList() {
    const files = fs.readdirSync(COOKIES_DIR);
    return files
        .filter(file => file.endsWith('.txt'))
        .map(file => file.replace('.txt', ''));
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
            '--window-size=1200,1200', // 设置浏览器窗口大小
            '--window-position=700,10' // 设置浏览器窗口位置，x=100, y=10
        ],
        ignoreHTTPSErrors: true,
        timeout: 30000
    });
}

async function automateTask(accountName) {
    const browser = await launchEdgeBrowser();
    const page = await browser.newPage();
    
    // 设置 Edge 的 User-Agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0');
    await page.setDefaultNavigationTimeout(30000);

    try {
        // 加载指定账号的cookies
        const hasCookies = await loadCookies(page, accountName);
        url = 'https://coupon.m.jd.com/coupons/show.action?linkKey=AAROH_xIpeffAs_-naABEFoeOSt_dda_7JxIYyDdjnkfedHrBWzZ4h_EaOKD1ZgII5ylfERlMzFo6opZhEvsugRbAkLCHg'
        
        await page.goto(url, {
            waitUntil: 'networkidle0',
            timeout: 3000000
        });

        // 点击"直接访问"链接
        try {

            // 检查是否存在"直接访问" 点击"直接访问"链接
            const directaccess = '#pcprompt-viewpc';
            const directaccessButton = await page.$(directaccess) !== null;
            if (directaccessButton) {
                await page.click('#pcprompt-viewpc', {
                    delay: Math.floor(Math.random() * 100) + 50
                });
                console.log(`账号 ${accountName}: 已点击直接访问链接`);
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
                    console.log(`账号 ${accountName}: 成功点击“一键领取”按钮`);

                    await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
                }else{
                    console.log("弹窗：",oneClickText);
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
                    console.log(`账号 ${accountName}: 成功点击“立即领取”按钮`);

                    await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
                }else{
                    console.log("弹窗：",YHJlijilinquText);
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
                    console.log(`账号 ${accountName}: 已点击`);
                    // 检测检查提示框是否存在，并且打印提示
                    const loginAlertSelector = '.mod_alert_v2.show.fixed';
                    const loginAlertVisible = await page.$(loginAlertSelector) !== null;
                    if (loginAlertVisible) {
                        // 获取提示框的文本内容
                        const alertText = await page.evaluate(selector => {
                            const alertElement = document.querySelector(selector);
                            return alertElement ? alertElement.textContent.trim() : '';
                        }, loginAlertSelector);
                        console.log("弹窗：",alertText);
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

            // *****************************************************检查是否存在商品优惠券信息
            const couponSelector = '.dicount_coupon .coupon';
            const couponElements = await page.$$(couponSelector);
            if (couponElements.length > 0) {
                // 获取所有的优惠券文本内容
                const couponsText = await page.evaluate(selector => {
                    const couponElements = document.querySelectorAll(selector);
                    return Array.from(couponElements).map(element => element.textContent.trim());
                }, couponSelector);

                // 输出所有的优惠券信息
                couponsText.forEach(coupon => {
                    console.log(`发现优惠券：${coupon}`);
                });

                // 示例：如果需要处理某个特定优惠券进入主见面
                const specificCoupon = '满1200减240'; // 这里可以根据需要修改
                if (couponsText.includes(specificCoupon)) {
                    console.log(`找到目标优惠券：${specificCoupon}`);
                    await page.click(couponSelector,{ delay: Math.floor(Math.random() * 100) + 50 });
                    await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
                    console.log(`账号 ${accountName}: 已点击`);

                    // 等待优惠券列表加载
                    await page.waitForSelector('#couponList');

                    // 获取所有优惠券的描述和按钮元素
                    const coupons = await page.$$('.coupon_voucher3');

                    for (const coupon of coupons) {
                        // 获取优惠券描述
                        const description = await coupon.$eval('.coupon_voucher3_view_des', el => el.textContent.trim());
                        
                        // 尝试获取按钮文本
                        let buttonText;
                        try {
                            buttonText = await coupon.$eval('.coupon_voucher3_info_btn', el => el.textContent.trim());
                        } catch (error) {
                            console.log(`未找到领取按钮，可能该优惠券不可用：${description}`);
                            continue; // 如果没有找到按钮，跳过此优惠券
                        }

                        // 检查按钮状态
                        const isDisabled = await coupon.$eval('.coupon_voucher3_info_btn', el => el.classList.contains('disabled'));
                        
                        // 进行精准领取的条件判断
                        if (!isDisabled) {
                            if (description.includes('满1200元可用') && buttonText === '领取') {
                                console.log(`找到可领取的优惠券：${description}`);
                                await coupon.$eval('.coupon_voucher3_info_btn', el => el.click());
                                await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
                                console.log(`账号 ${accountName}: 已领取优惠券 - ${description}`);

                            } else if (description.includes('满2000元可用') && buttonText === '领取') {
                                console.log(`找到可领取的优惠券：${description}`);
                                await coupon.$eval('.coupon_voucher3_info_btn', el => el.click());
                                await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
                                console.log(`账号 ${accountName}: 已领取优惠券 - ${description}`);
                                
                            } else if (description.includes('满1元可用') && buttonText === '领取') {
                                console.log(`找到可领取的优惠券：${description}`);
                                await coupon.$eval('.coupon_voucher3_info_btn', el => el.click());
                                await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
                                console.log(`账号 ${accountName}: 已领取优惠券 - ${description}`);
                            } else {
                                console.log(`优惠券不可领取或已领取：${description}，按钮文本：${buttonText}`);
                            }
                        } else {
                            console.log(`优惠券不可领取：${description}，按钮文本：${buttonText}`);
                        }
                    }

                } else {
                    console.log(`未找到目标优惠券：${specificCoupon}`);
                }

                await new Promise(resolve => setTimeout(resolve, 500)); // 等待响应500ms
            } else {
                console.log("未找到任何优惠券信息");
            }
            // *****************************************************检查是否存在商品优惠券信息


        } catch (error) {
            throw error;
        }

    } catch (error) {
        console.error(error.message);
        console.log('请检查网络连接并重试');
    } finally {
        // 添加关闭浏览器的代码
        console.log('结束');
        //await browser.close();
    }
}

async function addNewAccount(accountName) {
    const browser = await launchEdgeBrowser();
    const page = await browser.newPage();
    
    // 设置 Edge 的 User-Agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0');
    await page.setDefaultNavigationTimeout(30000);

    try {
        console.log('正在访问DJ登录页面...');
        await page.goto('https://plogin.m.jd.com/login/login', {
            waitUntil: 'networkidle0',
            timeout: 30000
        });
        
        console.log('请手动登录...');
        await page.waitForSelector('.jd-header-search-box', { 
            timeout: 0  // 无限等待用户登录
        });
        
        // 保存新账号的cookies
        await saveCookies(page, accountName);
        console.log(`新账号 ${accountName} 添加成功`);
        
    } catch (error) {
        console.error('添加账号时发生错误:', error.message);
        console.log('请检查网络连接并重试');
    } finally {
        await browser.close();
    }
}

// 正确导出模块
module.exports = {
    automateTask,
    addNewAccount,
    getAccountList
};
