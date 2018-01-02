
export async function fetchJson (url, fetchOptions) {
  let response = await fetch(url, fetchOptions)
  if (!response.ok) {
    let errorText = await response.text()
    throw new Error(`HTTP ${response.status} from ${response.url} : ${errorText}`)
  }
  return response.json()
}
