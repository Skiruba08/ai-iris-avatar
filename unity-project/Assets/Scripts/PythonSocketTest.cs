using UnityEngine;
using NativeWebSocket;
using System.IO;

public class PythonSocketTest : MonoBehaviour
{
    public string websocketUrl = "ws://127.0.0.1:8080/";
    public AudioSource audioSource;

    private WebSocket websocket;
    private int msgCounter = 0;

    async void Start()
    {
        websocket = new WebSocket(websocketUrl);

        websocket.OnOpen += () =>
        {
            Debug.Log("WebSocket connected.");
        };

        websocket.OnError += (e) =>
        {
            Debug.LogError("WebSocket error: " + e);
        };

        websocket.OnClose += (e) =>
        {
            Debug.Log("WebSocket closed.");
        };

        websocket.OnMessage += (bytes) =>
        {
            Debug.Log("Received audio bytes: " + bytes.Length);

            string path = Path.Combine(Application.persistentDataPath, "received_tts.wav");
            File.WriteAllBytes(path, bytes);
            Debug.Log("Saved WAV to: " + path);

            AudioClip clip = WavUtility.ToAudioClip(bytes, "tts_clip");
            if (clip != null)
            {
               audioSource.clip = clip;
               audioSource.volume = 1f;
               audioSource.spatialBlend = 0f;
               audioSource.pitch = 1f;
               audioSource.Play();

                Debug.Log("Playing audio.");
                Debug.Log("Clip length: " + clip.length);
                Debug.Log("Clip channels: " + clip.channels);
                Debug.Log("Clip frequency: " + clip.frequency);
            }
            else
            {
                Debug.LogError("Failed to convert WAV bytes to AudioClip.");
            }
        };

        await websocket.Connect();
    }

    async void Update()
{
#if !UNITY_WEBGL || UNITY_EDITOR
    websocket?.DispatchMessageQueue();
#endif

    if (Input.anyKeyDown)
    {
        Debug.Log("A key was pressed.");
    }

    if (websocket != null && websocket.State == WebSocketState.Open)
    {
        if (Input.GetKeyDown(KeyCode.Space))
        {
            Debug.Log("Space detected.");
            msgCounter++;

            string json =
                "{\"type\":\"query\",\"msgId\":\"" + msgCounter + "\",\"text\":\"Hello, this is a test of the text to speech system. Can you hear me clearly now?\"}";

            await websocket.SendText(json);
            Debug.Log("Sent test query: " + json);
        }
    }
}

    private async void OnApplicationQuit()
    {
        if (websocket != null)
            await websocket.Close();
    }
}