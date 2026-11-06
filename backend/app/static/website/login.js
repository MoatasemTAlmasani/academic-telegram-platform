(()=>{"use strict";
const $=id=>document.getElementById(id);
const loginForm=$("loginForm"),loginError=$("error"),loginButton=$("submit");
const recoveryPanel=$("recoveryPanel"),requestForm=$("recoveryRequestForm"),verifyForm=$("recoveryVerifyForm"),recoveryMessage=$("recoveryMessage");
const requestButton=$("recoveryRequestButton"),verifyButton=$("recoveryVerifyButton");
const copy={
 ar:{
  heading:"تسجيل الدخول",intro:"سجّل الدخول إلى حسابك للانتقال إلى مساحة الخدمات الخاصة بك.",username:"اسم المستخدم",password:"كلمة المرور",submit:"تسجيل الدخول",loading:"جارٍ التحقق…",bad:"اسم المستخدم أو كلمة المرور غير صحيحة.",failed:"تعذر تسجيل الدخول. حاول مرة أخرى.",verify:"تعذر التحقق من جلسة الدخول. يرجى المحاولة مجددًا.",foot:"سيتم استخدام حساب المنصة الحالي. لا يتم إنشاء حساب جديد من هذه الصفحة.",back:"العودة إلى الموقع الرسمي",forgot:"نسيت كلمة المرور؟",recoveryHeading:"استعادة كلمة المرور",recoveryIntro:"أدخل اسم المستخدم أو البريد الإلكتروني. إذا كان الحساب مرتبطًا بهوية Telegram موثّقة، فسنرسل رمز الاستعادة إليها.",identifier:"اسم المستخدم أو البريد الإلكترو٭���jם