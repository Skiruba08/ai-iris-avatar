using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Events;

using NativeWebSocket;


[Serializable]
public class WsMessageQuery
{
  public string type;
  public string text;
}

public enum WebSocketConnectionState
{
  Ok, Connecting, NotConnected
}


public class WebSocketClientBehaviour : MonoBehaviour
{
  [Tooltip("Address of the Python server e.g. 'ws://localhost:8080/'.")]
  public string websocketEndpoint = "ws://localhost:8080/";

  [Tooltip("Disable WebSocket. Use when e.g. testing with unity file.")]
  public bool disableWebsocket = false;


  [Tooltip("Called when received string from websocket.")]
  public UnityEvent<string> onJsonMessage;

  [Tooltip("Called when received WAV file bytes from websocket.")]
  public UnityEvent<byte[]> onWavBytesReceived;

  [Tooltip("Handlers for connection state.")]
  public UnityEvent<WebSocketClientBehaviour, WebSocketConnectionState> onConnectionChanged;

  [Tooltip("Handlers for sending new question to the server.")]
  public UnityEvent<string> onSendQuery;


  /// https://github.com/endel/NativeWebSocket
  private WebSocket websocket;
  private AudioSource audioComponent;

  private WebSocketConnectionState connectionState = WebSocketConnectionState.NotConnected;

  async void Start()
  {
    Debug.Log("WebSocket Start ran");
    Debug.Log("Connecting to websocket: " + websocketEndpoint);

    if (!disableWebsocket)
    {
      CreateWebSocket();
      if (websocket != null)
      {
        await websocket.Connect();
      }
    }
  }

  async public void Reconnect()
  {
    if (connectionState != WebSocketConnectionState.NotConnected) { return; }

    SetConnectionState(WebSocketConnectionState.Connecting);
    await websocket.Connect();
  }


  private void CreateWebSocket()
  {
    SetConnectionState(WebSocketConnectionState.Connecting);

    websocket = new WebSocket(this.websocketEndpoint);

    websocket.OnOpen += OnConnectionOpen;

    websocket.OnError += (e) =>
    {
      Debug.LogError("WebSocket error: " + e);
    };

    websocket.OnClose += (e) =>
    {
      SetConnectionState(WebSocketConnectionState.NotConnected);
      Debug.LogError("WebSocket connection closed! Code: " + e);
    };

    websocket.OnMessage += OnMessage;
  }


  void Update()
  {
#if !UNITY_WEBGL || UNITY_EDITOR
    if (websocket != null)
    {
      websocket.DispatchMessageQueue();
    }
#endif
  }

  void OnConnectionOpen()
  {
    Debug.Log("Connection open!");
    SetConnectionState(WebSocketConnectionState.Ok);
  }

  public async Task SendQuery(string prompt)
  {
    Debug.Log($"Query: '{prompt}'");

    var msg = new WsMessageQuery();
    msg.type = "query";
    msg.text = prompt;
    string json = JsonUtility.ToJson(msg);
    await websocket.SendText(json);

    onSendQuery?.Invoke(prompt);
  }

  private void SetConnectionState(WebSocketConnectionState s)
  {
    connectionState = s;
    onConnectionChanged?.Invoke(this, s);
  }

  private bool IsWavFileBytes(byte[] bytes)
  {
    if (bytes == null || bytes.Length < 4)
    {
      return false;
    }

    var ch0 = Convert.ToChar((int)bytes[0]);
    var ch1 = Convert.ToChar((int)bytes[1]);
    var ch2 = Convert.ToChar((int)bytes[2]);
    var ch3 = Convert.ToChar((int)bytes[3]);
    var asAscii = $"{ch0}{ch1}{ch2}{ch3}";
    return asAscii == "RIFF";
  }

  void OnMessage(byte[] bytes)
  {
    var isJson = !IsWavFileBytes(bytes);

    if (isJson)
    {
      var message = System.Text.Encoding.UTF8.GetString(bytes);
      Debug.Log($"OnMessage (string): {message}");

      onJsonMessage?.Invoke(message);
    }
    else
    {
      Debug.Log("OnMessage (bytes)");

      onWavBytesReceived?.Invoke(bytes);

      var speech = GetComponent<SpeechController>();
      if (speech != null)
      {
        speech.SpeakWavFileFromBytes(bytes);
      }
      else
      {
        Debug.LogError("SpeechController not found on this GameObject.");
      }
    }
  }

  private async void OnApplicationQuit()
  {
    if (websocket != null)
    {
      await websocket.Close();
    }
  }
}