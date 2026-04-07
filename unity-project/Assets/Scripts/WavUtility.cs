using System;
using UnityEngine;

public static class WavUtility
{
    public static AudioClip ToAudioClip(byte[] wavFile, string clipName = "wav")
    {
        try
        {
            int channels = BitConverter.ToInt16(wavFile, 22);
            int sampleRate = BitConverter.ToInt32(wavFile, 24);
            int bitsPerSample = BitConverter.ToInt16(wavFile, 34);

            int dataStartIndex = FindDataChunk(wavFile);
            if (dataStartIndex < 0)
            {
                Debug.LogError("WAV data chunk not found.");
                return null;
            }

            int dataSize = BitConverter.ToInt32(wavFile, dataStartIndex + 4);
            int audioDataStart = dataStartIndex + 8;

            int bytesPerSample = bitsPerSample / 8;
            int sampleCount = dataSize / bytesPerSample;

            float[] samples = new float[sampleCount];

            if (bitsPerSample == 16)
            {
                for (int i = 0; i < sampleCount; i++)
                {
                    short sample = BitConverter.ToInt16(wavFile, audioDataStart + i * 2);
                    samples[i] = Mathf.Clamp((sample / 32768f) * 12f, -1f, 1f);
                }
            }
            else
            {
                Debug.LogError("Only 16-bit WAV files are supported.");
                return null;
            }

            int frameCount = sampleCount / channels;
            AudioClip audioClip = AudioClip.Create(clipName, frameCount, channels, sampleRate, false);
            audioClip.SetData(samples, 0);
            return audioClip;
        }
        catch (Exception e)
        {
            Debug.LogError("WAV conversion failed: " + e.Message);
            return null;
        }
    }

    private static int FindDataChunk(byte[] wavFile)
    {
        for (int i = 12; i < wavFile.Length - 8; i++)
        {
            if (wavFile[i] == 'd' &&
                wavFile[i + 1] == 'a' &&
                wavFile[i + 2] == 't' &&
                wavFile[i + 3] == 'a')
            {
                return i;
            }
        }
        return -1;
    }
}