/**
 * Robokassa payment integration utility.
 *
 * Docs: https://docs.robokassa.ru/
 * Test mode uses test.robokassa.ru
 */

export interface RobokassaConfig {
  merchantLogin: string
  password1: string // For payment URL signature
  isTest: boolean
}

export interface PaymentParams {
  amount: number       // Sum in RUB
  invoiceId: number    // Unique invoice ID
  description: string  // Payment description (UTF-8)
  email?: string       // Customer email
  planId?: string      // Custom field: plan identifier
}

const DEFAULT_CONFIG: RobokassaConfig = {
  merchantLogin: import.meta.env.VITE_ROBOKASSA_MERCHANT_LOGIN || 'resumecraft',
  password1: import.meta.env.VITE_ROBOKASSA_PASSWORD1 || '',
  isTest: import.meta.env.VITE_ROBOKASSA_TEST_MODE !== 'false', // test by default
}

/**
 * Generate MD5 hash (browser-native via SubtleCrypto).
 * Robokassa requires MD5 signature: MerchantLogin:OutSum:InvId:Password1
 */
async function md5(message: string): Promise<string> {
  const msgBuffer = new TextEncoder().encode(message)
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

/**
 * Generate Robokassa payment URL.
 * In test mode → redirects to test.robokassa.ru
 * In production → redirects to auth.robokassa.ru
 */
export async function generatePaymentUrl(
  params: PaymentParams,
  config: RobokassaConfig = DEFAULT_CONFIG,
): Promise<string> {
  const { merchantLogin, password1, isTest } = config
  const { amount, invoiceId, description, email, planId } = params

  // Signature: MerchantLogin:OutSum:InvId:Password1
  const signatureStr = `${merchantLogin}:${amount.toFixed(2)}:${invoiceId}:${password1}`
  const signature = await md5(signatureStr)

  const baseUrl = isTest
    ? 'https://auth.robokassa.ru/Merchant/Index.aspx'
    : 'https://auth.robokassa.ru/Merchant/Index.aspx'

  const searchParams = new URLSearchParams({
    MerchantLogin: merchantLogin,
    OutSum: amount.toFixed(2),
    InvId: String(invoiceId),
    Description: description,
    SignatureValue: signature,
    Culture: 'ru',
    Encoding: 'utf-8',
    ...(isTest ? { IsTest: '1' } : {}),
    ...(email ? { Email: email } : {}),
    ...(planId ? { Shp_planId: planId } : {}),
  })

  return `${baseUrl}?${searchParams.toString()}`
}

/** Plan prices in RUB */
export const PLAN_PRICES: Record<string, number> = {
  standard: 490,
  pro: 1490,
}

/** Generate a pseudo-unique invoice ID based on timestamp */
export function generateInvoiceId(): number {
  return Math.floor(Date.now() / 1000) % 1_000_000_000
}
